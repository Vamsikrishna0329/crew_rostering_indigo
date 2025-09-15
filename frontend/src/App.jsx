import { useState } from "react";
import { generateRoster } from "./api";
import RosterTable from "./components/RosterTable";
import PatchForm from "./components/PatchForm";
import AIPanel from "./components/AIPanel";
import CalendarView from "./components/CalendarView";
import CrewGanttView from "./components/CrewGanttView";
import ConflictsPanel from "./components/ConflictsPanel";
import DisruptionsFeed from "./components/DisruptionsFeed";
import RuleClassification from "./components/RuleClassification";

export default function App() {
  const [start, setStart] = useState("2025-09-06");
  const [end, setEnd] = useState("2025-09-20");
  const [optimizationMethod, setOptimizationMethod] = useState("simple");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("roster");
  const [viewMode, setViewMode] = useState("table"); // table, calendar, gantt
  const [refreshKey, setRefreshKey] = useState(0); // Used to trigger refresh of calendar and gantt views

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await generateRoster({
        period_start: start,
        period_end: end,
        rules_version: "v1",
        optimization_method: optimizationMethod
      });
      setData(res);
      // Increment refresh key to trigger reload of calendar and gantt views
      setRefreshKey(prev => prev + 1);
    } catch (err) {
      setError("Failed to generate roster. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            {import.meta.env.VITE_APP_NAME || "Crew Rostering System"}
          </h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">Powered by Indigo</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {/* Date Selection Card */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  type="date"
                  value={start}
                  onChange={e => setStart(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  type="date"
                  value={end}
                  onChange={e => setEnd(e.target.value)}
                />
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Optimization Method</label>
                <select
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={optimizationMethod}
                  onChange={e => setOptimizationMethod(e.target.value)}
                >
                  <option value="simple">Simple Heuristics</option>
                  <option value="or_tools">OR-Tools (Advanced)</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={generate}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Generating...
                    </>
                  ) : "Generate Roster"}
                </button>
              </div>
            </div>
          </div>
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md">
              {error}
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab("roster")}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === "roster"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Roster
            </button>
            <button
              onClick={() => setActiveTab("rerostering")}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === "rerostering"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Re-rostering
            </button>
            <button
              onClick={() => setActiveTab("ai")}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === "ai"
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              AI Assistant
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === "roster" && (
            <div>
              {/* View Mode Selector */}
              <div className="mb-4 flex space-x-2">
                <button
                  onClick={() => setViewMode("table")}
                  className={`px-3 py-1 text-sm rounded-md ${
                    viewMode === "table"
                      ? "bg-blue-100 text-blue-700 font-medium"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Table View
                </button>
                <button
                  onClick={() => setViewMode("calendar")}
                  className={`px-3 py-1 text-sm rounded-md ${
                    viewMode === "calendar"
                      ? "bg-blue-100 text-blue-700 font-medium"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Calendar View
                </button>
                <button
                  onClick={() => setViewMode("gantt")}
                  className={`px-3 py-1 text-sm rounded-md ${
                    viewMode === "gantt"
                      ? "bg-blue-100 text-blue-700 font-medium"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Gantt View
                </button>
              </div>

              {/* Main Content Area with Sidebar */}
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Main Content */}
                <div className="flex-1">
                  {viewMode === "table" && <RosterTable data={data} loading={loading} />}
                  {viewMode === "calendar" && <CalendarView key={refreshKey} refreshKey={refreshKey} startDate={start} endDate={end} />}
                  {viewMode === "gantt" && <CrewGanttView key={refreshKey} refreshKey={refreshKey} startDate={start} endDate={end} />}
                </div>

                {/* Sidebar with Conflicts, Disruptions, and Rule Classification */}
                <div className="w-full lg:w-80 space-y-6">
                  <ConflictsPanel key={`conflicts-${refreshKey}`} refreshKey={refreshKey} startDate={start} endDate={end} />
                  <DisruptionsFeed key={`disruptions-${refreshKey}`} refreshKey={refreshKey} startDate={start} endDate={end} />
                  <RuleClassification key={`rules-${refreshKey}`} />
                </div>
              </div>
            </div>
          )}
          
          {activeTab === "rerostering" && (
            <div>
              <PatchForm />
            </div>
          )}
          
          {activeTab === "ai" && (
            <div>
              <AIPanel />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
