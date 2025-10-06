// Utility to format Pydantic validation errors into human-readable messages

interface ValidationError {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: any;
  ctx?: Record<string, any>;
  url?: string;
}

export const formatValidationErrors = (detail: any): string => {
  // If detail is a string, return it as is
  if (typeof detail === 'string') {
    return detail;
  }

  // If detail is an array of validation errors
  if (Array.isArray(detail)) {
    const errors = detail as ValidationError[];
    
    // Format each error into a readable message
    const messages = errors.map((error) => {
      const field = error.loc.slice(1).join(' -> '); // Skip 'body' prefix
      const fieldName = field || 'Field';
      
      // Custom messages based on error type
      switch (error.type) {
        case 'string_too_short':
          const minLength = error.ctx?.min_length || 0;
          return `${fieldName}: Must be at least ${minLength} characters (got ${typeof error.input === 'string' ? error.input.length : 0})`;
        
        case 'string_too_long':
          const maxLength = error.ctx?.max_length || 0;
          return `${fieldName}: Must be at most ${maxLength} characters`;
        
        case 'missing':
          return `${fieldName}: This field is required`;
        
        case 'value_error':
          return `${fieldName}: ${error.msg}`;
        
        case 'type_error':
          return `${fieldName}: Invalid type - ${error.msg}`;
        
        case 'datetime_parsing':
          return `${fieldName}: Invalid date format. Please use date picker or format: YYYY-MM-DD HH:MM:SS`;
        
        case 'int_parsing':
          return `${fieldName}: Must be a valid number`;
        
        case 'bool_parsing':
          return `${fieldName}: Must be true or false`;
        
        case 'json_invalid':
          return `${fieldName}: Invalid JSON format`;
        
        default:
          return `${fieldName}: ${error.msg}`;
      }
    });
    
    // Join all messages with line breaks
    return messages.join('\n');
  }

  // If detail is an object with detail property
  if (detail && typeof detail === 'object' && 'detail' in detail) {
    return formatValidationErrors(detail.detail);
  }

  // Fallback: stringify the object
  return JSON.stringify(detail);
};

export const handleApiError = (error: any, fallbackMessage: string = 'Operation failed'): string => {
  if (error.response?.data?.detail) {
    return formatValidationErrors(error.response.data.detail);
  }
  
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return fallbackMessage;
};
