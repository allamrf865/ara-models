import { AlertCircle } from "lucide-react";

interface AlertBarProps {
  alerts: any[];
}

export default function AlertBar({ alerts }: AlertBarProps) {
  if (alerts.length === 0) return null;

  return (
    <div className="bg-primary/10 border border-primary rounded-lg p-4">
      <div className="flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-primary flex-shrink-0" />
        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-4">
            {alerts.map((alert, i) => (
              <div key={i} className="flex items-center gap-2 whitespace-nowrap">
                <span className="font-mono font-bold">{alert.ticker}</span>
                <span className="text-sm text-muted-foreground">
                  Prob: {alert.proba.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
