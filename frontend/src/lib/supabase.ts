import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

/** True when the Supabase URL and public anon key are configured (.env.local). */
export const authConfigured = Boolean(url && anonKey && !url.includes("YOUR-PROJECT-REF"));

let client: SupabaseClient | null = null;

/**
 * Browser Supabase client, used only for sign-in. It holds the public anon key;
 * profile and history go through the FastAPI backend with the user's token.
 */
export function supabase(): SupabaseClient {
  if (!authConfigured) throw new Error("Sign-in isn't configured (NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY).");
  client ??= createClient(url!, anonKey!, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, storageKey: "airware-auth" },
  });
  return client;
}
