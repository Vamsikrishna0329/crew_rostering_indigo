import { useState, useEffect } from "react";
import { getRuleClassification } from "../api";

export default function RuleClassification() {
  const [classification, setClassification] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRuleClassification();
  }, []);

  const loadRuleClassification = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRuleClassification();
      setClassification(data.classification);
    } catch (err) {
      setError("Failed to load rule classification");
      console.error(err);
    } finally {
      setLoading(false);
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

  if (!classification) {
    return (
      <div className="text-center py-4">
        <p className="text-sm text-gray-500">No rule classification data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-md font-medium text-gray-800">Rule Classification</h3>
        <p className="text-xs text-gray-500 mt-1">Hard rules (non-negotiable) vs Soft rules (preferences/fairness)</p>
      </div>
      
      <div className="p-4">
        {/* Hard Rules Section */}
        <div className="mb-6">
          <div className="flex items-center mb-3">
            <div className="flex-shrink-0 w-3 h-3 rounded-full bg-red-500"></div>
            <h4 className="ml-2 text-sm font-semibold text-gray-900">Hard Rules (Non-Negotiable 🚫)</h4>
          </div>
          <p className="text-xs text-gray-600 mb-2">These are legal, safety, and contractual rules that must always be satisfied.</p>
          <ul className="space-y-2">
            {classification.hard_rules.map((rule, index) => (
              <li key={index} className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <span className="ml-2 text-xs text-gray-700">{rule}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Soft Rules Section */}
        <div>
          <div className="flex items-center mb-3">
            <div className="flex-shrink-0 w-3 h-3 rounded-full bg-green-500"></div>
            <h4 className="ml-2 text-sm font-semibold text-gray-900">Soft Rules (Desirable, Flexible ✔️)</h4>
          </div>
          <p className="text-xs text-gray-600 mb-2">These are preferences, fairness, and efficiency rules. The optimizer tries to maximize them.</p>
          <ul className="space-y-2">
            {classification.soft_rules.map((rule, index) => (
              <li key={index} className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-xs text-gray-700">{rule}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Summary */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-red-50 rounded-lg p-3">
              <div className="text-center">
                <div className="text-lg font-bold text-red-700">{classification.hard_rules.length}</div>
                <div className="text-xs text-red-600">Hard Rules</div>
              </div>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-center">
                <div className="text-lg font-bold text-green-700">{classification.soft_rules.length}</div>
                <div className="text-xs text-green-600">Soft Rules</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}