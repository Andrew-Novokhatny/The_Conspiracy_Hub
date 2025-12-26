import React, { useEffect, useRef } from 'react';
import { Streamlit, withStreamlitConnection } from 'streamlit-component-lib';
import { OpenSheetMusicDisplay } from 'opensheetmusicdisplay';

const MusicXMLViewer = (props) => {
  const osmdContainer = useRef(null);
  const osmd = useRef(null);

  useEffect(() => {
    if (osmdContainer.current && !osmd.current) {
      osmd.current = new OpenSheetMusicDisplay(osmdContainer.current, {
        autoResize: true,
        backend: 'svg',
        drawTitle: true,
        followCursor: false,
      });
    }
  }, []);

  useEffect(() => {
    const { xml_content } = props.args;
    if (xml_content && osmd.current) {
      osmd.current
        .load(xml_content)
        .then(() => {
          osmd.current.render();
          Streamlit.setFrameHeight();
        })
        .catch((error) => {
          console.error('OSMD Error:', error);
        });
    }
  }, [props.args.xml_content]);

  return (
    <div
      ref={osmdContainer}
      style={{
        background: 'white',
        padding: '1rem',
        borderRadius: '10px',
        boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
        minHeight: '400px',
      }}
    />
  );
};

export default withStreamlitConnection(MusicXMLViewer);
