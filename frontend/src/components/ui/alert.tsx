import React from 'react';

interface AlertProps {
  variant?: 'default' | 'destructive';
  className?: string;
  children: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({ variant = 'default', className = '', children }) => {
  const variantClasses = {
    default: 'bg-blue-50 border-blue-200 text-blue-900',
    destructive: 'bg-red-50 border-red-200 text-red-900'
  };

  return (
    <div className={`relative w-full rounded-lg border p-4 ${variantClasses[variant]} ${className}`}>
      {children}
    </div>
  );
};

interface AlertDescriptionProps {
  className?: string;
  children: React.ReactNode;
}

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ className = '', children }) => {
  return (
    <div className={`text-sm ${className}`}>
      {children}
    </div>
  );
};

interface AlertTitleProps {
  className?: string;
  children: React.ReactNode;
}

export const AlertTitle: React.FC<AlertTitleProps> = ({ className = '', children }) => {
  return (
    <h5 className={`mb-1 font-medium leading-none tracking-tight ${className}`}>
      {children}
    </h5>
  );
};
