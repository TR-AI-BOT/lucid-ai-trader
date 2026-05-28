import { cronJobs } from "convex/server";
import { internal } from "./_generated/api";

const crons = cronJobs();

// Reset dailyPnl at 9:30 AM ET (13:30 UTC) every trading day
// This ensures the daily loss limit resets correctly each morning
crons.weekly("reset daily pnl Monday",    { dayOfWeek: "monday",    hourUTC: 13, minuteUTC: 30 }, internal.accounts.resetAllDailyPnl);
crons.weekly("reset daily pnl Tuesday",   { dayOfWeek: "tuesday",   hourUTC: 13, minuteUTC: 30 }, internal.accounts.resetAllDailyPnl);
crons.weekly("reset daily pnl Wednesday", { dayOfWeek: "wednesday", hourUTC: 13, minuteUTC: 30 }, internal.accounts.resetAllDailyPnl);
crons.weekly("reset daily pnl Thursday",  { dayOfWeek: "thursday",  hourUTC: 13, minuteUTC: 30 }, internal.accounts.resetAllDailyPnl);
crons.weekly("reset daily pnl Friday",    { dayOfWeek: "friday",    hourUTC: 13, minuteUTC: 30 }, internal.accounts.resetAllDailyPnl);

export default crons;
