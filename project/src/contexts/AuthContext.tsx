import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User } from '@supabase/supabase-js';
import { supabase, UserType } from '../lib/supabase';

interface AuthContextType {
  user: User | null;
  userType: UserType;
  loading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [userType, setUserType] = useState<UserType>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      if (session?.user) {
        checkUserType(session.user.id);
      } else {
        setLoading(false);
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      (async () => {
        setUser(session?.user ?? null);
        if (session?.user) {
          await checkUserType(session.user.id);
        } else {
          setUserType(null);
          setLoading(false);
        }
      })();
    });

    return () => subscription.unsubscribe();
  }, []);

  async function checkUserType(userId: string) {
    const { data: official } = await supabase
      .from('officials')
      .select('id')
      .eq('id', userId)
      .maybeSingle();

    if (official) {
      setUserType('official');
    } else {
      setUserType('user');
    }
    setLoading(false);
  }

  async function signOut() {
    await supabase.auth.signOut();
    setUser(null);
    setUserType(null);
  }

  return (
    <AuthContext.Provider value={{ user, userType, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
