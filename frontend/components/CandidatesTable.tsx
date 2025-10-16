import { formatNumber } from "@/lib/utils";

interface CandidatesTableProps {
  data: any[];
  date: string;
  isLoading: boolean;
  error: any;
  highlightedTickers: Set<string>;
}

export default function CandidatesTable({
  data,
  date,
  isLoading,
  error,
  highlightedTickers,
}: CandidatesTableProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="h-12 bg-muted rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 text-center text-destructive">
        Error loading data: {error.message}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 text-center text-muted-foreground">
        No candidates available. Upload data via /score endpoint.
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      <div className="p-4 border-b border-border">
        <h2 className="text-xl font-semibold">Top Candidates</h2>
        <p className="text-sm text-muted-foreground">Date: {date}</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Rank</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Ticker</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Prob</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Nama</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Papan</th>
              <th className="px-4 py-3 text-right text-sm font-medium">VolRank</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr
                key={i}
                className={`border-b border-border hover:bg-muted/50 transition ${
                  highlightedTickers.has(row.Ticker) ? "bg-primary/20 animate-pulse" : ""
                }`}
              >
                <td className="px-4 py-3 text-sm">{i + 1}</td>
                <td className="px-4 py-3 text-sm font-mono font-semibold">{row.Ticker || "-"}</td>
                <td className="px-4 py-3 text-sm text-right font-bold text-primary">
                  {formatNumber(row.proba_ARA_t1 || 0, 4)}
                </td>
                <td className="px-4 py-3 text-sm">{row.nama || "-"}</td>
                <td className="px-4 py-3 text-sm capitalize">{row.Papan || "-"}</td>
                <td className="px-4 py-3 text-sm text-right">
                  {row.vol_rank_day ? formatNumber(row.vol_rank_day, 3) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
