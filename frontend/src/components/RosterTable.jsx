import { useState, useMemo } from "react";

export default function RosterTable({ data, loading }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });
  const [searchTerm, setSearchTerm] = useState("");

  const handleSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  const sortedAndFilteredData = useMemo(() => {
    if (!data || !data.assignments) return [];

    // Filter data based on search term
    let filtered = data.assignments;
    if (searchTerm) {
      filtered = data.assignments.filter(
        (assignment) =>
          (assignment.flight_id && assignment.flight_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (assignment.crew_name && assignment.crew_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (assignment.note && assignment.note.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Sort data
    if (sortConfig.key) {
      filtered = [...filtered].sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === "asc" ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === "asc" ? 1 : -1;
        }
        return 0;
      });
    }

    return filtered;
  }, [data, sortConfig, searchTerm]);

  const getSortIndicator = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === "asc" ? "↑" : "↓";
    }
    return "↕";
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-center items-center h-32">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-600">Generating roster...</span>
        </div>
      </div>
    );
  }

  if (!data || !data.assignments) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No roster generated</h3>
          <p className="mt-1 text-sm text-gray-500">Generate a roster to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Table Header with Search and Stats */}
      <div className="p-4 border-b border-gray-200 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Flight Assignments</h2>
          <p className="text-sm text-gray-500 mt-1">
            Showing {sortedAndFilteredData.length} of {data.assignments.length} assignments
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative">
            <input
              type="text"
              placeholder="Search assignments..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("flight_id")}
              >
                <div className="flex items-center">
                  Flight ID {getSortIndicator("flight_id")}
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("crew_id")}
              >
                <div className="flex items-center">
                  Crew ID {getSortIndicator("crew_id")}
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("crew_name")}
              >
                <div className="flex items-center">
                  Crew Name {getSortIndicator("crew_name")}
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("duty_start_utc")}
              >
                <div className="flex items-center">
                  Start (UTC) {getSortIndicator("duty_start_utc")}
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort("duty_end_utc")}
              >
                <div className="flex items-center">
                  End (UTC) {getSortIndicator("duty_end_utc")}
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Note
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedAndFilteredData.map((a, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{a.flight_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{a.crew_id ?? "-"}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{a.crew_name ?? "-"}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {a.duty_start_utc ? new Date(a.duty_start_utc).toLocaleString() : "-"}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {a.duty_end_utc ? new Date(a.duty_end_utc).toLocaleString() : "-"}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 max-w-xs">
                  <div className="truncate" title={a.note || ""}>
                    {a.note || "-"}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty State */}
      {sortedAndFilteredData.length === 0 && (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No assignments found</h3>
          <p className="mt-1 text-sm text-gray-500">Try adjusting your search filter</p>
        </div>
      )}

      {/* Stats Footer */}
      {data.kpis && (
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm font-medium text-gray-500">Total Flights</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">{data.kpis.flights_total}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm font-medium text-gray-500">Assigned Flights</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">{data.kpis.flights_assigned}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm font-medium text-gray-500">Assignment Rate</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {(data.kpis.assignment_rate * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm font-medium text-gray-500">Avg Preference Score</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {data.kpis.avg_preference_score?.toFixed(1) || "0.0"}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm font-medium text-gray-500">Fairness Score</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {(data.kpis.fairness_score * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm font-medium text-gray-500">Avg Duty per Crew</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {data.kpis.avg_duty_per_crew?.toFixed(1) || "0.0"}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm font-medium text-gray-500">Duty Range</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {data.kpis.duty_distribution_range || "0"}
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm font-medium text-gray-500">Compliance Rate</div>
              <div className="mt-1 text-2xl font-semibold text-gray-900">
                {(data.kpis.compliance_rate * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
