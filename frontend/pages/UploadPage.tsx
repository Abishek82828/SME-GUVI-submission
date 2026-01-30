import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createAssessment } from '../api/assessment';
import { addToHistory } from '../utils/history';

const INDUSTRIES = [
  'Retail',
  'Manufacturing',
  'Technology',
  'Services',
  'Construction',
  'Logistics',
  'Hospitality',
  'Healthcare',
  'Agriculture',
  'Other',
];

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Spanish' },
  { code: 'fr', label: 'French' },
];

const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [company, setCompany] = useState('');
  const [industry, setIndustry] = useState('');
  const [lang, setLang] = useState('en');

  const [files, setFiles] = useState<{
    sales: File | null;
    expenses: File | null;
    ar: File | null;
    ap: File | null;
    loans: File | null;
    inventory: File | null;
  }>({
    sales: null,
    expenses: null,
    ar: null,
    ap: null,
    loans: null,
    inventory: null,
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, field: keyof typeof files) => {
    if (e.target.files && e.target.files[0]) {
      setFiles((prev) => ({ ...prev, [field]: e.target.files![0] }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (company.trim().length < 2) {
      setError('Company name must be at least 2 characters.');
      return;
    }
    if (!industry) {
      setError('Please select an industry.');
      return;
    }
    if (!files.sales || !files.expenses) {
      setError('Sales and Expenses files are required.');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('company', company);
      formData.append('industry', industry);
      formData.append('lang', lang);
      
      if (files.sales) formData.append('sales', files.sales);
      if (files.expenses) formData.append('expenses', files.expenses);
      if (files.ar) formData.append('ar', files.ar);
      if (files.ap) formData.append('ap', files.ap);
      if (files.loans) formData.append('loans', files.loans);
      if (files.inventory) formData.append('inventory', files.inventory);

      const response = await createAssessment(formData);

      addToHistory({
        id: response.id,
        company: response.company,
        industry: response.industry,
        created_at: response.created_at,
      });

      navigate(`/assessments/${response.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create assessment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6 bg-blue-50 border-b border-blue-100">
          <h3 className="text-lg leading-6 font-medium text-blue-900">New Financial Assessment</h3>
          <p className="mt-1 max-w-2xl text-sm text-blue-700">Upload your financial documents to get started.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="px-4 py-5 sm:p-6 space-y-6">
          {error && (
            <div className="rounded-md bg-red-50 p-4 border border-red-200">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
            <div className="sm:col-span-3">
              <label htmlFor="company" className="block text-sm font-medium text-gray-700">
                Company Name <span className="text-red-500">*</span>
              </label>
              <div className="mt-1">
                <input
                  type="text"
                  name="company"
                  id="company"
                  required
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md border p-2"
                />
              </div>
            </div>

            <div className="sm:col-span-3">
              <label htmlFor="industry" className="block text-sm font-medium text-gray-700">
                Industry <span className="text-red-500">*</span>
              </label>
              <div className="mt-1">
                <select
                  id="industry"
                  name="industry"
                  required
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md border p-2 bg-white"
                >
                  <option value="">Select Industry</option>
                  {INDUSTRIES.map((ind) => (
                    <option key={ind} value={ind}>{ind}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="sm:col-span-3">
              <label htmlFor="lang" className="block text-sm font-medium text-gray-700">
                Language
              </label>
              <div className="mt-1">
                <select
                  id="lang"
                  name="lang"
                  value={lang}
                  onChange={(e) => setLang(e.target.value)}
                  className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md border p-2 bg-white"
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>{l.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-200 pt-6">
            <h4 className="text-sm font-medium text-gray-900 mb-4">Financial Documents</h4>
            <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Sales Data <span className="text-red-500">*</span></label>
                <input type="file" onChange={(e) => handleFileChange(e, 'sales')} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Expenses Data <span className="text-red-500">*</span></label>
                <input type="file" onChange={(e) => handleFileChange(e, 'expenses')} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Accounts Receivable (Optional)</label>
                <input type="file" onChange={(e) => handleFileChange(e, 'ar')} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Accounts Payable (Optional)</label>
                <input type="file" onChange={(e) => handleFileChange(e, 'ap')} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Loans (Optional)</label>
                <input type="file" onChange={(e) => handleFileChange(e, 'loans')} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Inventory (Optional)</label>
                <input type="file" onChange={(e) => handleFileChange(e, 'inventory')} className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100" />
              </div>

            </div>
          </div>

          <div className="pt-5">
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className={`ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                {loading ? 'Analyzing...' : 'Submit Assessment'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UploadPage;
