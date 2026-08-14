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
        this.speedSteps = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0];
        
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
            if (el) return el;
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
            // Ignore if typing in an input, textarea, or contenteditable
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

        // User manual scroll detection
        const container = this.getContainer();
        const scrollTarget = (container === document.documentElement || container === document.body) ? window : container;

        const onUserTouch = () => {
            this.userInteracting = true;
            clearTimeout(this.userInteractionTimeout);
            this.userInteractionTimeout = setTimeout(() => {
                this.userInteracting = false;
                this.lastTimestamp = null; // reset timestamp delta
            }, 300);
            this.updateProgress();
        };

        scrollTarget.addEventListener('wheel', onUserTouch, { passive: true });
        scrollTarget.addEventListener('touchstart', onUserTouch, { passive: true });
        scrollTarget.addEventListener('touchmove', onUserTouch, { passive: true });
        scrollTarget.addEventListener('scroll', () => this.updateProgress(), { passive: true });

        // Delegate Click events on document for controls
        document.addEventListener('click', (e) => {
            if (e.target.closest(this.playBtnSelector)) {
                e.preventDefault();
                this.togglePlay();
            } else if (e.target.closest(this.topBtnSelector)) {
                e.preventDefault();
                this.scrollToTop();
            } else if (e.target.closest(this.speedUpBtnSelector)) {
                e.preventDefault();
                this.increaseSpeed();
            } else if (e.target.closest(this.speedDownBtnSelector)) {
                e.preventDefault();
                this.decreaseSpeed();
            }
        });
    }

    getScrollStats() {
        const container = this.getContainer();
        const isWindow = (container === document.documentElement || container === document.body);
        
        const scrollTop = isWindow ? (window.pageYOffset || document.documentElement.scrollTop) : container.scrollTop;
        const scrollHeight = isWindow ? document.documentElement.scrollHeight : container.scrollHeight;
        const clientHeight = isWindow ? window.innerHeight : container.clientHeight;
        const maxScroll = Math.max(0, scrollHeight - clientHeight);

        return { scrollTop, scrollHeight, clientHeight, maxScroll, isWindow, container };
    }

    calculatePixelsPerSecond() {
        const { maxScroll } = this.getScrollStats();
        if (maxScroll <= 0) return 0;
        
        // Base duration in seconds
        const baseDuration = Math.max(30, this.durationSeconds);
        // Base pixels per second
        return maxScroll / baseDuration;
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

        // If we are at the very bottom, rewind to top first
        if (scrollTop >= maxScroll - 5) {
            this.scrollToTop(false);
        }

        this.isPlaying = true;
        this.lastTimestamp = null;
        this.updateUI();

        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = requestAnimationFrame((ts) => this.step(ts));
    }

    pause() {
        this.isPlaying = false;
        this.lastTimestamp = null;
        cancelAnimationFrame(this.animationFrameId);
        this.updateUI();
    }

    scrollToTop(smooth = true) {
        const { isWindow, container } = this.getScrollStats();
        if (isWindow) {
            window.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
        } else {
            container.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
        }
        this.subPixelAccumulator = 0;
        this.updateProgress();
    }

    setSpeed(newSpeed) {
        this.speed = Math.max(0.25, Math.min(4.0, parseFloat(newSpeed.toFixed(2))));
        this.updateUI();
    }

    increaseSpeed() {
        const next = this.speedSteps.find(s => s > this.speed + 0.05);
        this.setSpeed(next !== undefined ? next : this.speed + 0.25);
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
            const scrollDistance = pixelsPerSecond * this.speed * deltaSeconds;
            
            this.subPixelAccumulator += scrollDistance;
            const fullPixels = Math.floor(this.subPixelAccumulator);

            if (fullPixels > 0) {
                this.subPixelAccumulator -= fullPixels;
                const { isWindow, container, scrollTop, maxScroll } = this.getScrollStats();

                if (scrollTop >= maxScroll - 1) {
                    // Reached the end
                    this.pause();
                    return;
                }

                if (isWindow) {
                    window.scrollBy(0, fullPixels);
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
        // Update Play/Pause Buttons
        document.querySelectorAll(this.playBtnSelector).forEach(btn => {
            if (this.isPlaying) {
                btn.innerHTML = '<span class="autoscroll-icon">⏸️</span><span class="autoscroll-text">Pause</span>';
                btn.classList.add('is-playing');
                btn.setAttribute('aria-label', 'Pause Autoscroll (Space)');
            } else {
                btn.innerHTML = '<span class="autoscroll-icon">▶️</span><span class="autoscroll-text">Play</span>';
                btn.classList.remove('is-playing');
                btn.setAttribute('aria-label', 'Play Autoscroll (Space)');
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
