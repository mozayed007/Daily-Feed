const TOKEN_KEY = 'dailyfeed_access_token';
const REFRESH_KEY = 'dailyfeed_refresh_token';

export function setAccessToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setRefreshToken(token: string | null) {
  if (token) {
    localStorage.setItem(REFRESH_KEY, token);
  } else {
    localStorage.removeItem(REFRESH_KEY);
  }
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}
