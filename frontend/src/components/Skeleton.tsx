interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export function Skeleton({ className = '', variant = 'rectangular', width, height }: SkeletonProps) {
  const baseClass = 'animate-pulse bg-slate-200 dark:bg-slate-700';
  
  const variantClass = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  return (
    <div
      className={`${baseClass} ${variantClass[variant]} ${className}`}
      style={{ width, height }}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700">
      <Skeleton height={20} className="w-3/4 mb-3" />
      <Skeleton height={16} className="w-1/2 mb-4" />
      <Skeleton height={80} />
    </div>
  );
}

export function ArticleCardSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700">
      <div className="flex items-start gap-4">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="flex-1">
          <Skeleton height={16} className="w-1/4 mb-2" />
          <Skeleton height={24} className="w-3/4 mb-3" />
          <Skeleton height={60} />
          <div className="flex gap-2 mt-4">
            <Skeleton width={60} height={32} />
            <Skeleton width={60} height={32} />
            <Skeleton width={60} height={32} />
          </div>
        </div>
      </div>
    </div>
  );
}

export function StatsCardSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
      <Skeleton variant="circular" width={40} height={40} className="mb-3" />
      <Skeleton height={32} className="w-1/2 mb-1" />
      <Skeleton height={16} className="w-1/3" />
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700">
      <Skeleton height={20} className="w-1/3 mb-4" />
      <Skeleton height={200} />
    </div>
  );
}
