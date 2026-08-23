import type { ReactNode } from "react";

export interface TableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

export interface TableProps<T> {
  columns: TableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  /** Row keys that should render with the "expanded" highlight state. */
  expandedRowKeys?: (string | number)[];
  onRowClick?: (row: T) => void;
  emptyTitle?: string;
  emptyAction?: ReactNode;
}

/**
 * Base data Table — Frontend Design Document §5.
 * States: Default / Row-expanded / Empty. Empty state gives a next
 * action rather than just "no data" (§6 content & voice).
 */
export function Table<T>({
  columns,
  rows,
  rowKey,
  expandedRowKeys = [],
  onRowClick,
  emptyTitle = "Nothing here yet",
  emptyAction,
}: TableProps<T>) {
  if (rows.length === 0) {
    return (
      <div className="table-wrap">
        <div className="table-empty">
          <p>{emptyTitle}</p>
          {emptyAction && <div className="table-empty-action">{emptyAction}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const key = rowKey(row);
            const expanded = expandedRowKeys.includes(key);
            return (
              <tr
                key={key}
                className={expanded ? "table-row-expanded" : undefined}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                style={onRowClick ? { cursor: "pointer" } : undefined}
              >
                {columns.map((col) => (
                  <td key={col.key}>{col.render(row)}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
