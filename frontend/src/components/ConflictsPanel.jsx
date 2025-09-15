import { useState, useEffect } from "react";
import { getConflicts } from "../api";

export default function ConflictsPanel({ startDate, endDate, refreshKey }) {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    if (startDate && endDate) {
      loadConflicts();
    }
  }, [startDate, endDate, filter, refreshKey]);

  const loadConflicts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        start_date: startDate,
        end_date: endDate
      };
      
      if (filter !== "all") {
        params.severity = filter;
      }
      
      const data = await getConflicts(params);
      setConflicts(data.conflicts || []);
    } catch (err) {
      setError("Failed to load conflicts");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityClass = (severity) => {
    switch (severity) {
      case "high":
        return "bg-red-100 text-red-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getSeverityText = (severity) => {
    switch (severity) {
      case "high":
        return "High";
      case "medium":
        return "Medium";
      case "low":
        return "Low";
      default:
        return "Unknown";
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm">
        {error}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-md font-medium text-gray-800">Conflicts & Violations</h3>
        <div className="flex items-center space-x-2">
          <select
            className="text-xs border border-gray-300 rounded px-2 py-1"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Severity</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>
      
      <div className="p-3">
        {conflicts.length === 0 ? (
          <div className="text-center py-4">
            <svg className="mx-auto h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="mt-1 text-xs text-gray-500">No conflicts found</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {conflicts.map(conflict => (
              <div 
                key={conflict.id} 
                className="p-3 rounded-md border cursor-pointer hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSeverityClass(conflict.severity)}`}>
                        {getSeverityText(conflict.severity)}
                      </span>
                      <span className="ml-2 text-xs text-gray-500">#{conflict.id}</span>
                    </div>
                    <h4 className="mt-1 text-sm font-medium text-gray-900">{conflict.description}</h4>
                    <p className="mt-1 text-xs text-gray-500">
                      {conflict.crew_name} (ID: {conflict.crew_id})
                    </p>
                    {conflict.flight_ids && conflict.flight_ids.length > 0 && (
                      <p className="mt-1 text-xs text-gray-500">
                        Affected flights: {conflict.flight_ids.join(", ")}
                      </p>
                    )}
                  </div>
                  <div className="ml-2 text-xs text-gray-500 whitespace-nowrap">
                    {new Date(conflict.timestamp).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}