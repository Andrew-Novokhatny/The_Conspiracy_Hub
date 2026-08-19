/**
 * Band Hub - Stage & Lyrics Autoscroll Engine
 * Smooth, duration & tempo-aware teleprompter scrolling for musicians
 */

class LyricsAutoScroller {
    constructor(options = {}) {
        this.containerSelector = options.containerSelector || null;
        this.durationSeconds = parseFloat(options.durationSeconds) || 210;
        this.bpm = parseInt(options.bpm) || null;
        this.speed = parseFloat(options.speed) || 1.0;
        this.speedSteps = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0];
        
        this.isPlaying = false;
        this.lastTimestamp = null;
        this.subPixelAccumulator = 0;
        this.animationFrameId = null;
        this.userInteracting = false;
        this.userInteractionTimeout = null;

        // UI elements selectors
        this.playBtnSelector = options.playBtnSelector || '.autoscroll-play-btn';
        this.speedBadgeSelector = options.speedBadgeSelector || '.autoscroll-speed-badge';
        this.progressBarSelector = options.progressBarSelector || '.autoscroll-progress-fill';
        this.topBtnSelector = options.topBtnSelector || '.autoscroll-top-btn';
        this.speedUpBtnSelector = options.speedUpBtnSelector || '.autoscroll-faster-btn';
        this.speedDownBtnSelector = options.speedDownBtnSelector || '.autoscroll-slower-btn';

        this.init();
    }

    getContainer() {
        if (this.containerSelector) {
            const el = document.querySelector(this.containerSelector);
            if (el) {
                const style = window.getComputedStyle(el);
                const hasScrollOverflow = (style.overflowY === 'auto' || style.overflowY === 'scroll');
                if (hasScrollOverflow && el.scrollHeight > el.clientHeight + 10) {
                    return el;
                }
            }
        }
        return document.scrollingElement || document.documentElement || document.body;
    }

    init() {
        this.bindEvents();
        this.updateUI();
    }

    bindEvents() {
        // Keyboard Shortcuts
        document.addEventListener('keydown', (e) => {
            const tag = e.target.tagName.toLowerCase();
            if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) return;

            if (e.code === 'Space') {
                e.preventDefault();
                this.togglePlay();
            } else if (e.key === '+' || e.key === '=') {
                e.preventDefault();
                this.increaseSpeed();
            } else if (e.key === '-' || e.key === '_') {
                e.preventDefault();
                this.decreaseSpeed();
            } else if (e.key === 'Home' || (e.key.toLowerCase() === 'r' && !e.metaKey && !e.ctrlKey)) {
                e.preventDefault();
                this.scrollToTop();
            }
        });

        // User manual scroll detection - Ignore events on control bars
        const isControlElement = (target) => {
            if (!target) return false;
            return !!target.closest(
                '.lyrics-floating-autoscroll, .autoscroll-bar, .lyrics-inline-autoscroll, .show-stage-header, .show-bottom-bar, .autoscroll-btn, .autoscroll-speed-btn, .autoscroll-speed-group'
            );
        };

        const onUserManualTouch = (e) => {
            if (e && isControlElement(e.target)) return;
            this.userInteracting = true;
            clearTimeout(this.userInteractionTimeout);
            this.userInteractionTimeout = setTimeout(() => {
                this.userInteracting = false;
                this.lastTimestamp = null;
            }, 300);
            this.updateProgress();
        };

        window.addEventListener('wheel', onUserManualTouch, { passive: true });
        window.addEventListener('touchstart', onUserManualTouch, { passive: true });
        window.addEventListener('touchmove', onUserManualTouch, { passive: true });
        window.addEventListener('scroll', () => this.updateProgress(), { passive: true });

        // Bind control buttons with both click & touch handling
        const handleBtnAction = (e, actionFn) => {
            e.preventDefault();
            e.stopPropagation();
            actionFn.call(this);
        };

        document.addEventListener('click', (e) => {
            const playBtn = e.target.closest(this.playBtnSelector);
            if (playBtn) return handleBtnAction(e, this.togglePlay);

            const topBtn = e.target.closest(this.topBtnSelector);
            if (topBtn) return handleBtnAction(e, this.scrollToTop);

            const fasterBtn = e.target.closest(this.speedUpBtnSelector);
            if (fasterBtn) return handleBtnAction(e, this.increaseSpeed);

            const slowerBtn = e.target.closest(this.speedDownBtnSelector);
            if (slowerBtn) return handleBtnAction(e, this.decreaseSpeed);
        });
    }

    getScrollStats() {
        const container = this.getContainer();
        const isWindow = (
            container === document.documentElement || 
            container === document.body || 
            container === document.scrollingElement ||
            container === window
        );
        
        let scrollTop, scrollHeight, clientHeight;

        if (isWindow) {
            scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
            scrollHeight = Math.max(
                document.documentElement.scrollHeight || 0,
                document.body.scrollHeight || 0,
                document.documentElement.offsetHeight || 0,
                document.body.offsetHeight || 0
            );
            clientHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight || 0;
        } else {
            scrollTop = container.scrollTop;
            scrollHeight = container.scrollHeight;
            clientHeight = container.clientHeight;
        }
            
        const maxScroll = Math.max(0, scrollHeight - clientHeight);

        return { scrollTop, scrollHeight, clientHeight, maxScroll, isWindow, container };
    }

    calculatePixelsPerSecond() {
        const { maxScroll } = this.getScrollStats();
        if (maxScroll <= 0) return 0;
        
        const baseDuration = Math.max(30, this.durationSeconds);
        const pps = maxScroll / baseDuration;
        return Math.max(10, pps);
    }

    calculateEffectiveSpeed() {
        if (this.speed >= 2.0) {
            return Math.pow(this.speed, 1.35);
        }
        return this.speed;
    }

    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        const { maxScroll, scrollTop } = this.getScrollStats();
        if (maxScroll <= 0) return;

        // If at the very bottom, rewind to top first
        if (scrollTop >= maxScroll - 5) {
            this.scrollToTop(false);
        }

        this.isPlaying = true;
        this.lastTimestamp = null;
        this.userInteracting = false;
        this.subPixelAccumulator = 0;

        // Force scroll-behavior: auto to prevent browser smooth scroll throttling
        document.documentElement.classList.add('autoscroll-active');
        document.body.classList.add('autoscroll-active');
        document.documentElement.style.scrollBehavior = 'auto';
        document.body.style.scrollBehavior = 'auto';

        this.updateUI();

        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = requestAnimationFrame((ts) => this.step(ts));
    }

    pause() {
        this.isPlaying = false;
        this.lastTimestamp = null;
        this.subPixelAccumulator = 0;

        document.documentElement.classList.remove('autoscroll-active');
        document.body.classList.remove('autoscroll-active');
        document.documentElement.style.scrollBehavior = '';
        document.body.style.scrollBehavior = '';

        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        this.updateUI();
    }

    reset(durationSeconds, bpm) {
        this.pause();
        if (durationSeconds) this.durationSeconds = parseFloat(durationSeconds);
        this.bpm = bpm ? parseInt(bpm) : null;
        this.subPixelAccumulator = 0;
        this.lastTimestamp = null;
        this.scrollToTop(false);
        this.updateUI();
    }

    scrollToTop(smooth = true) {
        this.subPixelAccumulator = 0;
        this.lastTimestamp = null;
        const { isWindow, container } = this.getScrollStats();
        if (isWindow) {
            window.scrollTo({ top: 0, left: 0, behavior: smooth ? 'smooth' : 'instant' });
            document.documentElement.scrollTop = 0;
            document.body.scrollTop = 0;
        } else {
            container.scrollTo({ top: 0, left: 0, behavior: smooth ? 'smooth' : 'instant' });
            container.scrollTop = 0;
        }
        this.updateProgress();
    }

    setSpeed(newSpeed) {
        this.speed = Math.max(0.25, Math.min(4.0, parseFloat(newSpeed.toFixed(2))));
        this.updateUI();
    }

    increaseSpeed() {
        const next = this.speedSteps.find(s => s > this.speed + 0.05);
        this.setSpeed(next !== undefined ? next : Math.min(4.0, this.speed + 0.5));
    }

    decreaseSpeed() {
        const prev = [...this.speedSteps].reverse().find(s => s < this.speed - 0.05);
        this.setSpeed(prev !== undefined ? prev : Math.max(0.25, this.speed - 0.25));
    }

    step(timestamp) {
        if (!this.isPlaying) return;

        if (!this.lastTimestamp) {
            this.lastTimestamp = timestamp;
            this.animationFrameId = requestAnimationFrame((ts) => this.step(ts));
            return;
        }

        const deltaSeconds = (timestamp - this.lastTimestamp) / 1000;
        this.lastTimestamp = timestamp;

        if (!this.userInteracting) {
            const pixelsPerSecond = this.calculatePixelsPerSecond();
            const effectiveSpeed = this.calculateEffectiveSpeed();
            const scrollDistance = pixelsPerSecond * effectiveSpeed * deltaSeconds;
            
            this.subPixelAccumulator += scrollDistance;
            const fullPixels = Math.floor(this.subPixelAccumulator);

            if (fullPixels > 0) {
                this.subPixelAccumulator -= fullPixels;
                const { isWindow, container, scrollTop, maxScroll } = this.getScrollStats();

                if (scrollTop >= maxScroll - 1) {
                    this.pause();
                    return;
                }

                if (isWindow) {
                    const nextY = scrollTop + fullPixels;
                    window.scrollTo({ top: nextY, left: 0, behavior: 'instant' });
                    document.documentElement.scrollTop = nextY;
                    document.body.scrollTop = nextY;
                } else {
                    container.scrollTop += fullPixels;
                }
            }
        }

        this.updateProgress();
        this.animationFrameId = requestAnimationFrame((ts) => this.step(ts));
    }

    updateProgress() {
        const { scrollTop, maxScroll } = this.getScrollStats();
        const percent = maxScroll > 0 ? Math.min(100, Math.max(0, (scrollTop / maxScroll) * 100)) : 0;
        
        document.querySelectorAll(this.progressBarSelector).forEach(bar => {
            bar.style.width = `${percent}%`;
        });
    }

    updateUI() {
        // Update Play/Pause Buttons with minimalist SVG icons
        document.querySelectorAll(this.playBtnSelector).forEach(btn => {
            if (this.isPlaying) {
                btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg><span class="autoscroll-text">Pause</span>';
                btn.classList.add('is-playing');
                btn.setAttribute('aria-label', 'Pause Autoscroll (Space)');
            } else {
                btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"/></svg><span class="autoscroll-text">Play</span>';
                btn.classList.remove('is-playing');
                btn.setAttribute('aria-label', 'Play Autoscroll (Space)');
            }
        });

        // Update Top / Rewind buttons with minimalist SVG icon
        document.querySelectorAll(this.topBtnSelector).forEach(btn => {
            if (!btn.querySelector('svg')) {
                btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 6 12 11 7"/><polyline points="18 17 13 12 18 7"/></svg><span class="autoscroll-btn-label">Top</span>';
            }
        });

        // Update Speed Badges
        document.querySelectorAll(this.speedBadgeSelector).forEach(badge => {
            badge.textContent = `${this.speed.toFixed(this.speed % 1 === 0 ? 1 : 2)}x`;
        });

        this.updateProgress();
    }
}

// Helper to auto-initialize on pages that define autoscroll config
window.initLyricsAutoscroll = function(options = {}) {
    if (window.activeAutoScroller) {
        window.activeAutoScroller.pause();
    }
    window.activeAutoScroller = new LyricsAutoScroller(options);
    return window.activeAutoScroller;
};
