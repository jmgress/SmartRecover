import React, { useCallback, useEffect, useRef } from 'react';
import styles from './Resizer.module.css';

interface ResizerProps {
  onResize: (deltaX: number) => void;
}

export const Resizer: React.FC<ResizerProps> = ({ onResize }) => {
  const isDraggingRef = useRef(false);
  const startXRef = useRef(0);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    startXRef.current = e.clientX;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDraggingRef.current) return;
    
    const deltaX = e.clientX - startXRef.current;
    startXRef.current = e.clientX;
    onResize(deltaX);
  }, [onResize]);

  const handleMouseUp = useCallback(() => {
    if (isDraggingRef.current) {
      isDraggingRef.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  }, []);

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  return (
    <div
      className={styles.resizer}
      onMouseDown={handleMouseDown}
      role="separator"
      aria-label="Resize panels"
    >
      <div className={styles.handle} />
    </div>
  );
};
