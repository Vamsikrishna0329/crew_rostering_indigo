import { useState } from "react";
import { aiSuggest, aiAsk } from "../api";

export default function AIPanel() {
  const [flightNo, setFlightNo] = useState("6E1000");
  const [patch, setPatch] = useState(null);
  const [question, setQuestion] = useState("How many flights are loaded?");
  const [answer, setAnswer] = useState("");
  const [loadingSuggest, setLoadingSuggest] = useState(false);
  const [loadingAsk, setLoadingAsk] = useState(false);
  const [errorSuggest, setErrorSuggest] = useState(null);
  const [errorAsk, setErrorAsk] = useState(null);

  const suggest = async () => {
    setLoadingSuggest(true);
    setErrorSuggest(null);
    setPatch(null);

    try {
      const data = await aiSuggest(flightNo);
      setPatch(data);
    } catch (err) {
      setErrorSuggest("Failed to get AI suggestion. Please try again.");
      console.error(err);
    } finally {
      setLoadingSuggest(false);
    }
  };

  const ask = async () => {
    setLoadingAsk(true);
    setErrorAsk(null);
    setAnswer("");

    try {
      const { answer } = await aiAsk(question);
      setAnswer(answer);
    } catch (err) {
      setErrorAsk("Failed to get AI response. Please try again.");
      console.error(err);
    } finally {
      setLoadingAsk(false);
    }
  };

  const clearSuggest = () => {
    setPatch(null);
    setErrorSuggest(null);
  };

  const clearAsk = () => {
    setAnswer("");
    setErrorAsk(null);
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800">AI Assistant</h2>
        <p className="text-sm text-gray-500 mt-1">Get intelligent suggestions and answers for crew rostering</p>
      </div>
      
      <div className="p-6">
        {/* AI Reroster Suggestion Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-md font-medium text-gray-800">AI Re-rostering Suggestion</h3>
            <div className="flex items-center">
              <svg className="h-5 w-5 text-purple-500 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span className="text-sm text-purple-600 font-medium">AI-Powered</span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Flight Number</label>
              <input
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                value={flightNo}
                onChange={e => setFlightNo(e.target.value)}
                placeholder="Enter flight number"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={suggest}
                disabled={loadingSuggest}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loadingSuggest ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Analyzing...
                  </>
                ) : "Get Suggestion"}
              </button>
            </div>
          </div>

          {errorSuggest && (
            <div className="mt-2 p-3 bg-red-50 text-red-700 rounded-md">
              {errorSuggest}
            </div>
          )}

          {patch && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-700">Suggested Changes</h4>
                <button
                  onClick={clearSuggest}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                {patch.reassignments ? (
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Reassignment Suggestions</h5>
                    <ul className="space-y-2">
                      {patch.reassignments.map((reassignment, index) => (
                        <li key={index} className="border-b border-gray-200 pb-2">
                          {reassignment.from_crew_name ? (
                            <div>
                              <span className="font-medium">{reassignment.from_crew_name}</span>
                              {" → "}
                              <span className="font-medium">{reassignment.to_crew_name}</span>
                              {" for flight "}
                              <span className="font-medium">{reassignment.flight_no}</span>
                              {" (Score: "}{reassignment.preference_score}{")"}
                            </div>
                          ) : (
                            <div>
                              <span className="font-medium">{reassignment.crew_name}</span>
                              {" for flight "}
                              <span className="font-medium">{reassignment.to_flight}</span>
                              {" (Score: "}{reassignment.preference_score}{")"}
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                    <div className="mt-3 text-sm text-gray-600">
                      <strong>Message:</strong> {patch.message}
                    </div>
                  </div>
                ) : (
                  <pre className="text-sm text-gray-700 overflow-auto max-h-60">
                    {JSON.stringify(patch, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Ask the AI Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-md font-medium text-gray-800">Ask the AI</h3>
            <div className="flex items-center">
              <svg className="h-5 w-5 text-indigo-500 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span className="text-sm text-indigo-600 font-medium">Q&A</span>
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Your Question</label>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                className="flex-grow border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder="Ask anything about the roster..."
              />
              <button
                onClick={ask}
                disabled={loadingAsk}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loadingAsk ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Thinking...
                  </>
                ) : "Ask"}
              </button>
            </div>
          </div>

          {errorAsk && (
            <div className="mt-2 p-3 bg-red-50 text-red-700 rounded-md">
              {errorAsk}
            </div>
          )}

          {answer && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-700">AI Response</h4>
                <button
                  onClick={clearAsk}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              </div>
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-sm text-gray-700 whitespace-pre-wrap">
                  {answer}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
