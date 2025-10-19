"use client";

import { useAuth } from '@/lib/auth';
import LandingPage from '@/components/auth/landing-page';
import Dashboard from '@/components/dashboard';

export default function HomePage() {
  const { user } = useAuth();
  
  return user ? <Dashboard /> : <LandingPage />;
}
