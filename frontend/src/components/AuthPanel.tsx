import type { User } from "firebase/auth";
import { LogOut, UserRound } from "lucide-react";
import { useState } from "react";
import { firebaseEnabled, loginWithEmail, loginWithGoogle, logout } from "../lib/firebase";

interface AuthPanelProps {
  user: User | null;
}

export function AuthPanel({ user }: AuthPanelProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  if (!firebaseEnabled) {
    return (
      <div className="auth-panel">
        <UserRound aria-hidden />
        <span>Development auth enabled</span>
      </div>
    );
  }

  if (user) {
    return (
      <div className="auth-panel">
        <UserRound aria-hidden />
        <span>{user.email}</span>
        <button onClick={() => void logout()} aria-label="Sign out">
          <LogOut aria-hidden />
        </button>
      </div>
    );
  }

  return (
    <form
      className="auth-form"
      onSubmit={(event) => {
        event.preventDefault();
        void loginWithEmail(email, password);
      }}
    >
      <input placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} />
      <input
        placeholder="Password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      <button type="submit">Sign in</button>
      <button type="button" onClick={() => void loginWithGoogle()}>
        Google
      </button>
    </form>
  );
}

