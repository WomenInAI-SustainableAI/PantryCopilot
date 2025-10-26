// Runtime configuration - can be changed without rebuilding
export const getApiBaseUrl = () => {
  // When served from backend, use relative path
  return process.env.NEXT_PUBLIC_API_URL || '/api';
};
export const getBaseUrl = () => {
  return process.env.NEXT_PUBLIC_BASE_URL || '';
}