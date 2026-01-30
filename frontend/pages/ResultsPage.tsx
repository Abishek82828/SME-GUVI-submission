import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getAssessment, getAssessmentReport, getAssessmentAI } from '../api/assessment';
import { addToHistory } from '../utils/history';
import { AssessmentResponse } from '../types';

const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<AssessmentResponse | null>(null);
  const [reportMd, setReportMd] = useState<string>('');
  const [aiMd, setAiMd] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      try {
        // Fetch core assessment first to ensure ID validity
        const assessment = await getAssessment(id);
        
        // Then fetch reports (ignoring errors on optional parts if necessary)
        const [report, ai] = await Promise.all([
          getAssessmentReport(id).catch(err => {
            console.warn('Failed to fetch report', err);
            return '';
          }),
          getAssessmentAI(id).catch(err => {
            console.warn('Failed to fetch AI report', err);
            return '';
          })
        ]);

        setData(assessment);
        setReportMd(report);
        setAiMd(ai);

        addToHistory({
          id: assessment.id,
          company: assessment.company,
          industry: assessment.industry,
          created_at: assessment.created_at,
        });

      } catch (err: any) {
        console.error(err);
        setError(err.message || 'Failed to load assessment results.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleDownloadReport = () => {
    if (!reportMd) return;
    const blob = new Blob([reportMd], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${data?.company || 'assessment'}_report.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
  
  if (error) return (
    <div className="max-w-7xl mx-auto py-10 px-4">
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Error: </strong>
        <span className="block sm:inline">{error}</span>
      </div>
    </div>
  );
  
  if (!data || !data.result_json) return <div className="text-center py-20 text-gray-500">No data found.</div>;

  const { result_json: res } = data;

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      
      {/* Header */}
      <div className="bg-white shadow rounded-lg px-6 py-5 border-l-4 border-blue-600">
        <h1 className="text-2xl font-bold text-gray-900">{data.company}</h1>
        <div className="mt-2 text-sm text-gray-500 flex flex-wrap gap-4">
          <span className="bg-gray-100 px-2 py-1 rounded">Industry: {data.industry}</span>
          <span className="bg-gray-100 px-2 py-1 rounded">Date: {new Date(data.created_at).toLocaleDateString()}</span>
          <span className="bg-gray-100 px-2 py-1 rounded">ID: {data.id}</span>
        </div>
      </div>

      {/* Scores */}
      {res.scores && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'Health Score', value: res.scores.health_score, color: 'text-green-600' },
            { label: 'Risk Score', value: res.scores.risk_score, color: 'text-red-600' },
            { label: 'Credit Readiness', value: res.scores.credit_readiness_score, color: 'text-blue-600' },
            { label: 'Rating', value: res.scores.rating, color: 'text-purple-600' },
          ].map((score) => (
            <div key={score.label} className="bg-white overflow-hidden shadow rounded-lg p-5 text-center">
              <dt className="text-sm font-medium text-gray-500 truncate">{score.label}</dt>
              <dd className={`mt-1 text-3xl font-semibold ${score.color}`}>{score.value}</dd>
            </div>
          ))}
        </div>
      )}

      {/* KPIs */}
      {res.kpis && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Key Performance Indicators</h3>
          </div>
          <div className="px-6 py-5 grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-500">Revenue</p>
              <p className="text-lg font-medium">{res.kpis.total_revenue?.toLocaleString() ?? '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Expense</p>
              <p className="text-lg font-medium">{res.kpis.total_expense?.toLocaleString() ?? '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Operating Margin</p>
              <p className="text-lg font-medium">{res.kpis.operating_margin ? (res.kpis.operating_margin * 100).toFixed(1) + '%' : '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Runway (Months)</p>
              <p className="text-lg font-medium">{res.kpis.runway_months_proxy?.toFixed(1) ?? '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">DSO (Days)</p>
              <p className="text-lg font-medium">{res.kpis.dso_days?.toFixed(0) ?? '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">DPO (Days)</p>
              <p className="text-lg font-medium">{res.kpis.dpo_days?.toFixed(0) ?? '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">EMI Ratio</p>
              <p className="text-lg font-medium">{res.kpis.emi_to_monthly_revenue ? (res.kpis.emi_to_monthly_revenue * 100).toFixed(1) + '%' : '-'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Risks */}
      {res.risks && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Risk Assessment</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Signal</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {res.risks.map((risk, idx) => (
                  <tr key={idx}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                        ${(risk.severity || '').toLowerCase() === 'high' ? 'bg-red-100 text-red-800' : 
                          (risk.severity || '').toLowerCase() === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                        {risk.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{risk.type}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{risk.signal}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{risk.why}</td>
                  </tr>
                ))}
                {res.risks.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">No significant risks detected.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {res.recommendations && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recommendations</h3>
          </div>
          <ul className="divide-y divide-gray-200">
            {res.recommendations.map((rec, idx) => (
              <li key={idx} className="px-6 py-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="text-md font-bold text-gray-900">{rec.title}</h4>
                    <p className="mt-1 text-sm text-gray-600">{rec.why}</p>
                    <ul className="mt-2 list-disc list-inside text-sm text-gray-500">
                      {(rec.actions || []).map((action, i) => <li key={i}>{action}</li>)}
                    </ul>
                  </div>
                  <span className="ml-4 inline-flex items-center px-2.5 py-0.5 rounded-md text-sm font-medium bg-blue-100 text-blue-800">
                    Impact: {rec.impact_estimate}
                  </span>
                </div>
              </li>
            ))}
            {res.recommendations.length === 0 && (
              <li className="px-6 py-4 text-center text-sm text-gray-500">No specific recommendations.</li>
            )}
          </ul>
        </div>
      )}

      {/* Forecast Table */}
      {res.forecast && res.forecast.forecast && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Forecast ({res.forecast.horizon_months} Months)</h3>
            <p className="text-sm text-gray-500 mt-1">Method: {res.forecast.method}</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Month</th>
                  <th className="px-6 py-3 text-right font-medium text-gray-500">Rev Forecast</th>
                  <th className="px-6 py-3 text-right font-medium text-gray-500">Exp Forecast</th>
                  <th className="px-6 py-3 text-right font-medium text-gray-500">Op Profit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {res.forecast.forecast.map((f, i) => (
                  <tr key={i}>
                    <td className="px-6 py-3 whitespace-nowrap text-gray-900">{f.month}</td>
                    <td className="px-6 py-3 whitespace-nowrap text-right text-gray-600">{f.forecast_revenue?.toLocaleString()}</td>
                    <td className="px-6 py-3 whitespace-nowrap text-right text-gray-600">{f.forecast_expense?.toLocaleString()}</td>
                    <td className={`px-6 py-3 whitespace-nowrap text-right font-medium ${f.forecast_operating_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {f.forecast_operating_profit?.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Breakdowns */}
      {res.breakdowns && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Financial Breakdowns</h3>
          </div>
          <div className="px-6 py-5 bg-gray-50">
            <pre className="text-xs text-gray-600 overflow-auto">{JSON.stringify(res.breakdowns, null, 2)}</pre>
          </div>
        </div>
      )}

      {/* Benchmarks (Conditional) */}
      {res.benchmarks && res.benchmarks.available && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Industry Benchmarks ({res.benchmarks.industry})</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(res.benchmarks.benchmarks || {}).map(([key, val]) => (
              <div key={key} className="border p-4 rounded bg-gray-50">
                <span className="block text-xs font-bold text-gray-500 uppercase">{key.replace(/_/g, ' ')}</span>
                <div className="flex justify-between items-end mt-2">
                   <div>
                     <span className="text-sm text-gray-400">Industry</span>
                     <p className="font-semibold text-gray-700">{val as React.ReactNode}</p>
                   </div>
                   <div className="text-right">
                     <span className="text-sm text-gray-400">You</span>
                     <p className={`font-semibold ${res.benchmarks.gaps?.[key] === 'Low' ? 'text-green-600' : 'text-blue-600'}`}>
                       {res.benchmarks.your?.[key]}
                     </p>
                   </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Analysis (New) */}
      {aiMd && (
        <div className="bg-white shadow rounded-lg overflow-hidden border border-purple-200">
          <div className="px-6 py-5 border-b border-purple-100 bg-purple-50">
            <h3 className="text-lg leading-6 font-medium text-purple-900">AI Deep Analysis</h3>
          </div>
          <div className="px-6 py-5 bg-white overflow-auto max-h-[600px]">
            <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">{aiMd}</pre>
          </div>
        </div>
      )}

      {/* Report Markdown */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Detailed Report</h3>
          <button 
            onClick={handleDownloadReport}
            disabled={!reportMd}
            className={`inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none ${!reportMd ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            Download .md
          </button>
        </div>
        <div className="px-6 py-5 bg-gray-50 overflow-auto max-h-[500px]">
          <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">{reportMd || 'Report not available.'}</pre>
        </div>
      </div>

      {/* Debug Data */}
      <details className="bg-gray-100 rounded p-4">
        <summary className="cursor-pointer text-sm text-gray-500 font-medium">Debug Raw JSON</summary>
        <pre className="mt-2 text-xs text-gray-600 overflow-auto">{JSON.stringify(res, null, 2)}</pre>
      </details>
      
    </div>
  );
};

export default ResultsPage;
