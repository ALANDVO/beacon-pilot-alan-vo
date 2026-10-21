/** Loading Spinner Component */
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  return (
    <div className={`loading-spinner ${size} ${className}`} role="status" aria-label="Loading">
      <div className="spinner" />
      <span className="sr-only">Loading...</span>
    </div>
  );
}