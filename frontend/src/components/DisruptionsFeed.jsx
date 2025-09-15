import { useState, useEffect } from "react";
import { getDisruptions } from "../api";

export default function DisruptionsFeed({ startDate, endDate, refreshKey }) {
  const [disruptions, setDisruptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    if (startDate && endDate) {
      loadDisruptions();
    }
  }, [startDate, endDate, filter, refreshKey]);

  const loadDisruptions = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        start_date: startDate,
        end_date: endDate
      };
      
      if (filter !== "all") {
        params.disruption_type = filter;
      }
      
      const data = await getDisruptions(params);
      setDisruptions(data.disruptions || []);
    } catch (err) {
      setError("Failed to load disruptions");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getTypeClass = (type) => {
    switch (type) {
      case "delay":
        return "bg-blue-100 text-blue-800";
      case "cancellation":
        return "bg-red-100 text-red-800";
      case "crew_unavailability":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getTypeText = (type) => {
    switch (type) {
      case "delay":
        return "Delay";
      case "cancellation":
        return "Cancellation";
      case "crew_unavailability":
        return "Crew Unavailability";
      default:
        return type;
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
        <h3 className="text-md font-medium text-gray-800">Disruptions Feed</h3>
        <div className="flex items-center space-x-2">
          <select
            className="text-xs border border-gray-300 rounded px-2 py-1"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Types</option>
            <option value="delay">Delays</option>
            <option value="cancellation">Cancellations</option>
            <option value="crew_unavailability">Crew Unavailability</option>
          </select>
        </div>
      </div>
      
      <div className="p-3">
        {disruptions.length === 0 ? (
          <div className="text-center py-4">
            <svg className="mx-auto h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <p className="mt-1 text-xs text-gray-500">No disruptions found</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {disruptions.map(disruption => (
              <div 
                key={disruption.id} 
                className="p-3 rounded-md border hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getTypeClass(disruption.type)}`}>
                        {getTypeText(disruption.type)}
                      </span>
                      <span className="ml-2 text-xs text-gray-500">#{disruption.id}</span>
                    </div>
                    <h4 className="mt-1 text-sm font-medium text-gray-900">
                      {disruption.flight_no ? `Flight ${disruption.flight_no}` : "Crew Issue"}
                    </h4>
                    <p className="mt-1 text-xs text-gray-500">
                      {disruption.reason || "No reason provided"}
                    </p>
                    {disruption.crew_id && (
                      <p className="mt-1 text-xs text-gray-500">
                        Crew ID: {disruption.crew_id}
                      </p>
                    )}
                    {disruption.impact_duration && (
                      <p className="mt-1 text-xs text-gray-500">
                        Impact: {disruption.impact_duration} minutes
                      </p>
                    )}
                    {disruption.resolution && (
                      <p className="mt-1 text-xs text-green-600">
                        Resolution: {disruption.resolution}
                      </p>
                    )}
                  </div>
                  <div className="ml-2 text-xs text-gray-500 whitespace-nowrap">
                    {new Date(disruption.date).toLocaleDateString()}
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