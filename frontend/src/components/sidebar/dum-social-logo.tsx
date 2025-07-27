'use client';

import Image from 'next/image';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

interface DumSocialLogoProps {
  size?: number;
  className?: string;
}

export function DumSocialLogo({ size = 24, className }: DumSocialLogoProps) {
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // After mount, we can access the theme
  useEffect(() => {
    setMounted(true);
  }, []);

  const shouldInvert = mounted && (
    theme === 'dark' || (theme === 'system' && systemTheme === 'dark')
  );

  return (
    <Image
      src="/dum-social-logo.svg"
      alt="Dum Social"
      width={size}
      height={size}
      className={`${shouldInvert ? 'invert' : ''} flex-shrink-0 ${className || ''}`}
    />
  );
}
