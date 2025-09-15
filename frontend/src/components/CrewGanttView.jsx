import { useState, useEffect } from "react";
import { getCrewGantt } from "../api";

export default function CrewGanttView({ startDate, endDate, refreshKey }) {
  const [crewData, setCrewData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (startDate && endDate) {
      loadGanttData();
    }
  }, [startDate, endDate, refreshKey]);

  const loadGanttData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCrewGantt({
        start_date: startDate,
        end_date: endDate
      });
      setCrewData(data.crew_data || []);
    } catch (err) {
      setError("Failed to load Gantt data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-md">
        {error}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800">Crew Gantt View</h2>
        <p className="text-sm text-gray-500 mt-1">Each crew member's row shows duty and rest periods</p>
      </div>
      
      <div className="p-6">
        {crewData.length === 0 ? (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No crew data</h3>
            <p className="mt-1 text-sm text-gray-500">Generate a roster to see the Gantt view</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Crew Member</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Base</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duties</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {crewData.map(crew => (
                  <tr key={crew.crew_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{crew.crew_name}</div>
                      <div className="text-sm text-gray-500">ID: {crew.crew_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {crew.crew_role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {crew.base_iata}
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-2">
                        {crew.duties.map(duty => (
                          <div key={duty.id} className="flex items-center p-2 bg-gray-50 rounded-md">
                            <div className="flex-shrink-0 w-2 h-2 rounded-full bg-green-500"></div>
                            <div className="ml-2 flex-1">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{duty.flight_no}</p>
                                  <p className="text-xs text-gray-500">{duty.dep_iata} → {duty.arr_iata} ({duty.aircraft_code})</p>
                                </div>
                                <div className="text-right">
                                  <p className="text-xs text-gray-500">{formatTime(duty.start)} - {formatTime(duty.end)}</p>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}