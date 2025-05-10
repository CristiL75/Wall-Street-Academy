export const isAuthenticated = () => {
    const token = localStorage.getItem("access_token");
    return !!token;
  };
  
  export const logout = () => {
    localStorage.removeItem("access_token");
  };

  export const getTokenPayload = () => {
    const token = localStorage.getItem("access_token");
    if (!token) return null;
  
    try {
      const payload = token.split(".")[1];
      return JSON.parse(atob(payload));
    } catch (e) {
      console.error("Invalid token", e);
      return null;
    }
  };

  