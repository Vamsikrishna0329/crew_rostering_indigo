import { useState } from "react";
import { rerosterDelay } from "../api";

export default function PatchForm() {
  const [flightNo, setFlightNo] = useState("6E1000");
  const [disruptionType, setDisruptionType] = useState("Delay");
  const [delay, setDelay] = useState(45);
  const [crewId, setCrewId] = useState("");
  const [unavailableFrom, setUnavailableFrom] = useState("");
  const [unavailableTo, setUnavailableTo] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const validateForm = () => {
    if (!flightNo.trim()) {
      setError("Flight number is required");
      return false;
    }
    
    if (disruptionType === "Delay" && delay <= 0) {
      setError("Delay must be a positive number");
      return false;
    }
    
    if (disruptionType === "CrewUnavailability") {
      if (!crewId.trim()) {
        setError("Crew ID is required for crew unavailability");
        return false;
      }
      if (!unavailableFrom.trim()) {
        setError("Unavailable from date is required");
        return false;
      }
      if (!unavailableTo.trim()) {
        setError("Unavailable to date is required");
        return false;
      }
    }
    
    return true;
  };

  const submit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let data;
      if (disruptionType === "Delay") {
        data = await rerosterDelay({
          flight_no: flightNo,
          type: "Delay",
          delay_minutes: Number(delay)
        });
      } else if (disruptionType === "Cancellation") {
        data = await rerosterDelay({
          flight_no: flightNo,
          type: "Cancellation"
        });
      } else if (disruptionType === "CrewUnavailability") {
        data = await rerosterDelay({
          flight_no: flightNo,
          type: "CrewUnavailability",
          crew_id: Number(crewId),
          unavailable_from: unavailableFrom,
          unavailable_to: unavailableTo
        });
      }
      setResult(data);
    } catch (err) {
      setError("Failed to process re-rostering request. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const clearResult = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800">Flight Re-rostering</h2>
        <p className="text-sm text-gray-500 mt-1">Adjust crew assignments for flight disruptions</p>
      </div>
      
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Disruption Type</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={disruptionType}
              onChange={e => setDisruptionType(e.target.value)}
            >
              <option value="Delay">Flight Delay</option>
              <option value="Cancellation">Flight Cancellation</option>
              <option value="CrewUnavailability">Crew Unavailability</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Flight Number</label>
            <input
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={flightNo}
              onChange={e => setFlightNo(e.target.value)}
              placeholder="e.g. 6E1000"
            />
          </div>
        </div>
        
        {disruptionType === "Delay" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Delay (minutes)</label>
              <input
                type="number"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={delay}
                onChange={e => setDelay(e.target.value)}
                placeholder="Delay in minutes"
                min="1"
              />
            </div>
          </div>
        )}
        
        {disruptionType === "CrewUnavailability" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Crew ID</label>
              <input
                type="number"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={crewId}
                onChange={e => setCrewId(e.target.value)}
                placeholder="Crew ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unavailable From</label>
              <input
                type="date"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={unavailableFrom}
                onChange={e => setUnavailableFrom(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unavailable To</label>
              <input
                type="date"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={unavailableTo}
                onChange={e => setUnavailableTo(e.target.value)}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}

        <div className="mt-6">
          <button
            onClick={submit}
            disabled={loading}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </>
            ) : "Propose Re-rostering"}
          </button>
          
          {(result || error) && (
            <button
              onClick={clearResult}
              className="ml-3 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-md transition duration-200"
            >
              Clear
            </button>
          )}
        </div>

        {result && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-md font-medium text-gray-800">Re-rostering Results</h3>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Success
              </span>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <pre className="text-sm text-gray-700 overflow-auto max-h-96">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
