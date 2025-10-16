import { Download } from "lucide-react";

interface FilterPanelProps {
  k: number;
  setK: (k: number) => void;
  liq: number;
  setLiq: (liq: number) => void;
  excludePemantauan: boolean;
  setExcludePemantauan: (exclude: boolean) => void;
  onDownload: () => void;
}

export default function FilterPanel({
  k,
  setK,
  liq,
  setLiq,
  excludePemantauan,
  setExcludePemantauan,
  onDownload,
}: FilterPanelProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Filters</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Top K</label>
          <select
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="w-full bg-background border border-border rounded px-3 py-2"
          >
            {[10, 20, 30, 50, 100].map((val) => (
              <option key={val} value={val}>
                {val}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Min Liquidity: {liq.toFixed(2)}</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={liq}
            onChange={(e) => setLiq(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div className="flex items-end gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={excludePemantauan}
              onChange={(e) => setExcludePemantauan(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm">Exclude Pemantauan Khusus</span>
          </label>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <button
          onClick={onDownload}
          className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 transition"
        >
          <Download className="w-4 h-4" />
          Download CSV
        </button>
      </div>
    </div>
  );
}
