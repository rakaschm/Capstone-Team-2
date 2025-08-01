import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

function InterestTag({ label }) {
  return (
    <span
      className="inline-block px-4 py-2 bg-gray-200 rounded-lg text-gray-800 text-base font-medium mr-2 mb-2"
      tabIndex="0"
      aria-label={`Interest: ${label}`}
    >
      {label}
    </span>
  );
}

InterestTag.propTypes = {
  label: PropTypes.string.isRequired,
};

export function UserProfile({ userId, onRecommendationsClick }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Example API endpoint: /api/users/{userId}
  useEffect(() => {
    setLoading(true);
    fetch(`/api/users/${userId}`)
      .then((res) => res.json())
      .then((data) => setUser(data))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return (
      <div className="h-80 flex items-center justify-center">Loading...</div>
    );
  }

  if (!user) {
    return (
      <div className="h-80 flex items-center justify-center text-red-600">
        User not found.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-md p-8 max-w-xs w-full mx-auto">
      {/* Avatar */}
      <div className="flex justify-center">
        <img
          src={user.avatarUrl}
          alt={`Profile of ${user.name}`}
          className="w-24 h-24 rounded-full mb-4 border-4 border-blue-100 object-cover"
        />
      </div>
      {/* Name */}
      <h1 className="text-3xl font-bold text-center mb-4">{user.name}</h1>
      {/* Interests */}
      <div>
        <p className="font-bold text-lg mb-2">Interests</p>
        <div className="flex flex-wrap">
          {user.interests.map((interest) => (
            <InterestTag key={interest} label={interest} />
          ))}
        </div>
      </div>

      {/* Recommendations Button */}
      <button
        className="mt-8 w-full bg-teal-600 text-white font-semibold text-xl py-3 rounded-lg shadow-md transition hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-400"
        onClick={onRecommendationsClick}
        aria-label="Show recommendations based on interests"
      >
        RECOMMENDATIONS
      </button>
    </div>
  );
}

UserProfile.propTypes = {
  userId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  onRecommendationsClick: PropTypes.func,
};

UserProfile.defaultProps = {
  onRecommendationsClick: () => {},
};

export default UserProfile;