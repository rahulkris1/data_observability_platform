import React from 'react';

export interface RuleActivationToggleProps {
  ruleId: string;
  enabled: boolean;
  ruleName: string;
  onToggle: (ruleId: string, enabled: boolean) => Promise<void>;
  disabled?: boolean;
}

export default function RuleActivationToggle({
  ruleId,
  enabled,
  ruleName,
  onToggle,
  disabled = false
}: RuleActivationToggleProps) {
  const [isToggling, setIsToggling] = React.useState(false);
  const [currentState, setCurrentState] = React.useState(enabled);
  
  React.useEffect(() => {
    setCurrentState(enabled);
  }, [enabled]);
  
  const handleToggle = async () => {
    if (disabled || isToggling) return;
    
    setIsToggling(true);
    const newState = !currentState;
    
    try {
      await onToggle(ruleId, newState);
      setCurrentState(newState);
    } catch (error) {
      console.error('Failed to toggle rule:', error);
      // Revert on error
      setCurrentState(!newState);
    } finally {
      setIsToggling(false);
    }
  };
  
  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={handleToggle}
        disabled={disabled || isToggling}
        className={`
          relative inline-flex h-6 w-11 items-center rounded-full
          transition-colors duration-200 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${currentState ? 'bg-green-600' : 'bg-gray-300'}
          ${disabled || isToggling ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        aria-label={`${currentState ? 'Disable' : 'Enable'} rule ${ruleName}`}
        title={`${currentState ? 'Disable' : 'Enable'} this rule`}
      >
        <span
          className={`
            inline-block h-4 w-4 transform rounded-full bg-white
            transition-transform duration-200 ease-in-out
            ${currentState ? 'translate-x-6' : 'translate-x-1'}
          `}
        />
      </button>
      
      <span className={`text-sm font-medium ${currentState ? 'text-green-700' : 'text-gray-500'}`}>
        {isToggling ? 'Updating...' : currentState ? 'Enabled' : 'Disabled'}
      </span>
    </div>
  );
}
