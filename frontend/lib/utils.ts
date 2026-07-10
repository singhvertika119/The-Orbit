/**
 * Joins truthy class name values together.
 */
export function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ')
}

/**
 * Formats a number to the Indian Rupee (INR) system.
 * Example: 150000 -> "₹1,50,000.00"
 */
export function formatCurrency(value: number | string): string {
  const numericValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numericValue)) return '₹0.00'
  
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(numericValue)
}

/**
 * Formats an ISO date string to a standard readable format.
 * Example: "2026-07-15" -> "15 Jul 2026"
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return dateString
    
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    })
  } catch (e) {
    return dateString
  }
}
