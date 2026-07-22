"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { penceToPoundsDisplay } from "@marketplays/shared";
import { sellerCardClass } from "@/components/seller/seller-styles";
import type { MonthlyRevenuePoint } from "@/components/seller/stub-data";

interface RevenueChartProps {
  data: MonthlyRevenuePoint[];
}

/** 12-month revenue bar chart — seller utility panel. */
export function RevenueChart({ data }: RevenueChartProps) {
  const chartData = data.map((d) => ({
    month: d.month,
    revenue: d.revenuePence / 100,
  }));

  return (
    <section className={`${sellerCardClass} p-5`}>
      <h2 className="text-[16px] font-bold text-[#F5F6F8]">
        Revenue · 12 months
      </h2>
      <div className="mt-2 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1D2330" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fill: "#6B7280", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#6B7280", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `£${v}`}
              width={48}
            />
            <Tooltip
              cursor={{ fill: "#1D233080" }}
              contentStyle={{
                background: "#10141C",
                border: "1px solid #262C38",
                borderRadius: 8,
                fontSize: 12,
                color: "#F5F6F8",
              }}
              formatter={(value) => {
                const pounds =
                  typeof value === "number" ? value : Number(value ?? 0);
                return [
                  penceToPoundsDisplay(Math.round(pounds * 100)),
                  "Revenue",
                ];
              }}
            />
            <Bar dataKey="revenue" fill="#3B5BFF" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
