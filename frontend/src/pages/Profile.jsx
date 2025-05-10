import { useEffect, useState } from "react";
import { getTokenPayload } from "../utils/auth";
import axios from "axios";

const Profile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const payload = getTokenPayload();
        if (!payload?.sub) return;

        const token = localStorage.getItem("token");

        const res = await axios.get(`http://127.0.0.1:8000/users/${payload.sub}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        setUser(res.data);
      } catch (err) {
        console.error("Error fetching user info:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  if (loading) return <p className="p-6">Loading profile...</p>;
  if (!user) return <p className="p-6 text-red-500">User not found.</p>;

  const formattedDate = user.created_at
    ? new Date(user.created_at).toLocaleDateString("ro-RO", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "N/A";

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">👤 Profilul tău</h1>
      <div className="bg-white shadow rounded p-4 space-y-2">
        <p><strong>Username:</strong> {user.username || "N/A"}</p>
        <p><strong>Email:</strong> {user.email || "N/A"}</p>
        <p>
          <strong>Wallet Address:</strong>{" "}
          <code className="text-sm break-all">{user.wallet_address || "N/A"}</code>
        </p>
        <p><strong>Creat la:</strong> {formattedDate}</p>
      </div>
    </div>
  );
};

export default Profile;
