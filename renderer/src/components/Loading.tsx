import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' };

export function Spinner({ size = 'md', label, className = '' }: SpinnerProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Loader2 className={`${sizes[size]} animate-spin text-indigo-600`} />
      {label && <span className="text-sm text-gray-500">{label}</span>}
    </div>
  );
}

interface PageLoaderProps {
  label?: string;
}

export function PageLoader({ label = '加载中...' }: PageLoaderProps) {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      <span className="text-sm text-gray-500">{label}</span>
    </div>
  );
}

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = 'h-4 w-full' }: SkeletonProps) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className}`} />;
}

export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
      <Skeleton className="h-32 w-full rounded-lg" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  );
}
