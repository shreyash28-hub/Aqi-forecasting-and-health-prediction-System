import { Suspense } from "react";
import type { Metadata } from "next";
import { SignInView } from "@/components/auth/sign-in-view";

export const metadata: Metadata = { title: "Sign in" };

export default function SignInPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-page" />}>
      <SignInView />
    </Suspense>
  );
}
