import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

// Child: Individual row
const PropertyRow = ({ property }) => (
  <tr className="even:bg-gray-50 hover:bg-amber-50 transition-colors">
    <td className="p-4 whitespace-nowrap">{property.name}</td>
    <td className="p-4">{property.city}, {property.state}</td>
    <td className="p-4">{property.address_line1}</td>
    <td className="p-4">{property.amenities.join(", ")}</td>
    <td className="p-4 font-semibold">${property.price_per_night}</td>
  </tr>
);

PropertyRow.propTypes = {
  property: PropTypes.shape({
    name: PropTypes.string.isRequired,
    location: PropTypes.string.isRequired,
    address: PropTypes.string.isRequired,
    amenities: PropTypes.array.isRequired,
    price_per_night: PropTypes.number.isRequired
  }).isRequired
};

// Main Table Component
const PropertyTable = ({ apiUrl }) => {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(apiUrl)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch properties");
        return res.json();
      })
      .then((data) => {
        setProperties(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [apiUrl]);

  if (loading)
    return (
      <div className="p-8 text-center text-gray-500 animate-pulse">
        <span role="img" aria-label="loading" className="mr-2">⏳</span>
        Searching for your perfect getaway...
      </div>
    );
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
  if (properties.length === 0) return <div className="p-8 text-center text-gray-400">No properties found.</div>;

  return (
    <div className="overflow-x-auto rounded-lg border bg-white">
      <table className="min-w-full text-sm text-left">
        <thead className="bg-orange-100">
          <tr>
            <th scope="col" className="px-6 py-3 font-semibold">🏨 Property Name</th>
            <th scope="col" className="px-6 py-3 font-semibold">📍 Location</th>
            <th scope="col" className="px-6 py-3 font-semibold">🗺️ Address</th>
            <th scope="col" className="px-6 py-3 font-semibold">🛎️ Amenities</th>
            <th scope="col" className="px-6 py-3 font-semibold">💵 Price per Night</th>
          </tr>
        </thead>
        <tbody>
          {properties.map((property) => (
            <PropertyRow key={property.id} property={property} />
          ))}
        </tbody>
      </table>
    </div>
  );
};

PropertyTable.propTypes = {
  apiUrl: PropTypes.string.isRequired
};

export default PropertyTable;