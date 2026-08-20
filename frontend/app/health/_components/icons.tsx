// Local to Member 1's health module - dependency-free inline SVGs, mirrors
// the pattern in components/icons.tsx but kept here so this module has no
// shared-file edits to coordinate.

export function ClipboardIcon({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <rect x="6" y="4" width="12" height="17" rx="2" />
      <path strokeLinecap="round" d="M9 4V3a1 1 0 011-1h4a1 1 0 011 1v1" />
      <path strokeLinecap="round" d="M9 11h6M9 15h6" />
    </svg>
  );
}

export function DocumentSearchIcon({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" />
      <path strokeLinecap="round" d="M14 3v5h5" />
      <circle cx="10.5" cy="15.5" r="2" />
      <path strokeLinecap="round" d="M12.2 17.2L14 19" />
    </svg>
  );
}

export function StethoscopeIcon({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 3v6a4 4 0 008 0V3" />
      <path strokeLinecap="round" d="M9 13v2a5 5 0 005 5 5 5 0 005-5v-1" />
      <circle cx="19" cy="8" r="2" />
    </svg>
  );
}

export function LeafIcon({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 21c8 0 14-6 14-14V5h-2C9 5 5 11 5 19v2z" />
      <path strokeLinecap="round" d="M5 21c4-4 6-8 6-12" />
    </svg>
  );
}

export function SmileIcon({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <circle cx="12" cy="12" r="9" />
      <path strokeLinecap="round" d="M8.5 10.5h.01M15.5 10.5h.01" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 14.5c1 1.2 2.4 1.8 4 1.8s3-.6 4-1.8" />
    </svg>
  );
}
