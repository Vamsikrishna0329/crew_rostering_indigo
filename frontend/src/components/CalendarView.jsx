import { useState, useEffect } from "react";
import { getRosterCalendar } from "../api";

export default function CalendarView({ startDate, endDate, refreshKey }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("weekly"); // daily, weekly, monthly
  const [currentDate, setCurrentDate] = useState(new Date());

  useEffect(() => {
    if (startDate && endDate) {
      loadCalendarData();
    }
  }, [startDate, endDate, refreshKey]);

  const loadCalendarData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRosterCalendar({
        start_date: startDate,
        end_date: endDate
      });
      setEvents(data.events || []);
    } catch (err) {
      setError("Failed to load calendar data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Navigation functions
  const goToPrevious = () => {
    const newDate = new Date(currentDate);
    if (viewMode === "daily") {
      newDate.setDate(newDate.getDate() - 1);
    } else if (viewMode === "weekly") {
      newDate.setDate(newDate.getDate() - 7);
    } else {
      newDate.setMonth(newDate.getMonth() - 1);
    }
    setCurrentDate(newDate);
  };

  const goToNext = () => {
    const newDate = new Date(currentDate);
    if (viewMode === "daily") {
      newDate.setDate(newDate.getDate() + 1);
    } else if (viewMode === "weekly") {
      newDate.setDate(newDate.getDate() + 7);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // Format time for display
  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Format date for display
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Get date range for current view
  const getViewDateRange = () => {
    const start = new Date(currentDate);
    const end = new Date(currentDate);
    
    if (viewMode === "daily") {
      end.setDate(end.getDate() + 1);
    } else if (viewMode === "weekly") {
      // Get Monday of the current week
      const day = start.getDay();
      const diff = start.getDate() - day + (day === 0 ? -6 : 1); // Adjust for Sunday
      start.setDate(diff);
      end.setDate(start.getDate() + 7);
    } else {
      // Monthly view
      start.setDate(1);
      end.setMonth(start.getMonth() + 1);
      end.setDate(0); // Last day of the month
    }
    
    return { start, end };
  };

  // Get events for a specific date
  const getEventsForDate = (date) => {
    return events.filter(event => {
      const eventDate = new Date(event.start).toISOString().split('T')[0];
      const currentDateStr = date.toISOString().split('T')[0];
      return eventDate === currentDateStr;
    });
  };

  // Get events for a date range
  const getEventsForRange = (start, end) => {
    return events.filter(event => {
      const eventStart = new Date(event.start);
      return eventStart >= start && eventStart < end;
    });
  };

  // Daily view component
  const DailyView = () => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const date = currentDate;
    
    return (
      <div className="flex flex-col h-full">
        <div className="text-center py-2 border-b">
          <h3 className="text-lg font-semibold">
            {date.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </h3>
        </div>
        <div className="flex-1 overflow-y-auto">
          {hours.map(hour => {
            const hourEvents = events.filter(event => {
              const eventStart = new Date(event.start);
              return eventStart.getDate() === date.getDate() &&
                     eventStart.getMonth() === date.getMonth() &&
                     eventStart.getFullYear() === date.getFullYear() &&
                     eventStart.getHours() === hour;
            });
            
            return (
              <div key={hour} className="flex border-b">
                <div className="w-20 py-2 text-right pr-2 text-sm text-gray-500 border-r">
                  {hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`}
                </div>
                <div className="flex-1 min-h-16 relative">
                  {hourEvents.map(event => (
                    <div 
                      key={event.id} 
                      className="absolute left-0 right-0 mx-1 my-0.5 rounded text-xs p-1 truncate"
                      style={{ 
                        top: `${(new Date(event.start).getMinutes() / 60) * 100}%`,
                        height: `${((new Date(event.end) - new Date(event.start)) / (1000 * 60 * 60)) * 100}%`,
                        backgroundColor: `${event.color}20`,
                        borderLeft: `3px solid ${event.color}`
                      }}
                    >
                      <div className="font-medium">{event.flight_no}</div>
                      <div className="truncate">{event.crew_name}</div>
                      <div>{formatTime(event.start)} - {formatTime(event.end)}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Weekly view component
  const WeeklyView = () => {
    const { start } = getViewDateRange();
    const days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date(start);
      date.setDate(date.getDate() + i);
      return date;
    });
    
    const hours = Array.from({ length: 24 }, (_, i) => i);
    
    return (
      <div className="flex flex-col h-full">
        <div className="grid grid-cols-8 border-b">
          <div className="p-2"></div>
          {days.map(day => (
            <div key={day.toISOString()} className="p-2 text-center">
              <div className="font-medium">{day.toLocaleDateString(undefined, { weekday: 'short' })}</div>
              <div className={`text-sm ${day.toDateString() === new Date().toDateString() ? 'bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center mx-auto' : ''}`}>
                {day.getDate()}
              </div>
            </div>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto">
          {hours.map(hour => (
            <div key={hour} className="grid grid-cols-8">
              <div className="p-1 text-right pr-2 text-xs text-gray-500 border-r">
                {hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`}
              </div>
              {days.map(day => {
                const cellEvents = events.filter(event => {
                  const eventStart = new Date(event.start);
                  return eventStart.getDate() === day.getDate() &&
                         eventStart.getMonth() === day.getMonth() &&
                         eventStart.getFullYear() === day.getFullYear() &&
                         eventStart.getHours() === hour;
                });
                
                return (
                  <div key={`${day.toISOString()}-${hour}`} className="min-h-12 border-r relative">
                    {cellEvents.map(event => (
                      <div 
                        key={event.id} 
                        className="absolute left-0 right-0 mx-1 my-0.5 rounded text-xs p-1 truncate"
                        style={{ 
                          top: `${(new Date(event.start).getMinutes() / 60) * 100}%`,
                          height: `${((new Date(event.end) - new Date(event.start)) / (1000 * 60 * 60)) * 100}%`,
                          backgroundColor: `${event.color}20`,
                          borderLeft: `3px solid ${event.color}`
                        }}
                      >
                        <div className="font-medium">{event.flight_no}</div>
                        <div className="truncate">{event.crew_name}</div>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Monthly view component
  const MonthlyView = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // First day of the month
    const firstDay = new Date(year, month, 1);
    // Last day of the month
    const lastDay = new Date(year, month + 1, 0);
    // First day of the calendar (Sunday of the week that includes the first day)
    const startDay = new Date(firstDay);
    startDay.setDate(firstDay.getDate() - firstDay.getDay());
    // Last day of the calendar (Saturday of the week that includes the last day)
    const endDay = new Date(lastDay);
    endDay.setDate(lastDay.getDate() + (6 - lastDay.getDay()));
    
    // Generate all days to display
    const days = [];
    const currentDay = new Date(startDay);
    while (currentDay <= endDay) {
      days.push(new Date(currentDay));
      currentDay.setDate(currentDay.getDate() + 1);
    }
    
    // Group days by week
    const weeks = [];
    for (let i = 0; i < days.length; i += 7) {
      weeks.push(days.slice(i, i + 7));
    }
    
    return (
      <div className="flex flex-col h-full">
        <div className="grid grid-cols-7 border-b">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="p-2 text-center font-medium text-gray-700">
              {day}
            </div>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto">
          {weeks.map((week, weekIndex) => (
            <div key={weekIndex} className="grid grid-cols-7">
              {week.map(day => {
                const dayEvents = getEventsForDate(day);
                const isCurrentMonth = day.getMonth() === month;
                const isToday = day.toDateString() === new Date().toDateString();
                
                return (
                  <div 
                    key={day.toISOString()} 
                    className={`min-h-24 border-r border-b p-1 ${!isCurrentMonth ? 'bg-gray-50' : ''}`}
                  >
                    <div className={`text-right p-1 ${isToday ? 'bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center ml-auto' : ''}`}>
                      {day.getDate()}
                    </div>
                    <div className="space-y-1 mt-1">
                      {dayEvents.slice(0, 3).map(event => (
                        <div 
                          key={event.id} 
                          className="text-xs p-1 rounded truncate"
                          style={{ 
                            backgroundColor: `${event.color}20`,
                            borderLeft: `2px solid ${event.color}`
                          }}
                        >
                          <div className="font-medium truncate">{event.flight_no}</div>
                          <div className="truncate">{event.crew_name}</div>
                        </div>
                      ))}
                      {dayEvents.length > 3 && (
                        <div className="text-xs text-gray-500">
                          +{dayEvents.length - 3} more
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-md">
        {error}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Roster Calendar</h2>
            <p className="text-sm text-gray-500 mt-1">Daily/weekly/monthly roster visualization</p>
          </div>
          
          {/* View mode selector */}
          <div className="flex space-x-2">
            <button
              onClick={() => setViewMode("daily")}
              className={`px-3 py-1 text-sm rounded-md ${
                viewMode === "daily"
                  ? "bg-blue-100 text-blue-700 font-medium"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Day
            </button>
            <button
              onClick={() => setViewMode("weekly")}
              className={`px-3 py-1 text-sm rounded-md ${
                viewMode === "weekly"
                  ? "bg-blue-100 text-blue-700 font-medium"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setViewMode("monthly")}
              className={`px-3 py-1 text-sm rounded-md ${
                viewMode === "monthly"
                  ? "bg-blue-100 text-blue-700 font-medium"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Month
            </button>
          </div>
        </div>
        
        {/* Navigation controls */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center space-x-2">
            <button
              onClick={goToPrevious}
              className="p-2 rounded-md hover:bg-gray-100"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path>
              </svg>
            </button>
            <button
              onClick={goToToday}
              className="px-3 py-1 text-sm bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Today
            </button>
            <button
              onClick={goToNext}
              className="p-2 rounded-md hover:bg-gray-100"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>
          
          <div className="text-lg font-medium">
            {viewMode === "daily" && currentDate.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            {viewMode === "weekly" && (() => {
              const { start, end } = getViewDateRange();
              const options = { month: 'short', day: 'numeric' };
              return `${start.toLocaleDateString(undefined, options)} - ${end.toLocaleDateString(undefined, options)}`;
            })()}
            {viewMode === "monthly" && currentDate.toLocaleDateString(undefined, { year: 'numeric', month: 'long' })}
          </div>
          
          <div className="w-24"></div> {/* Spacer for alignment */}
        </div>
      </div>
      
      <div className="flex-1 p-4">
        {viewMode === "daily" && <DailyView />}
        {viewMode === "weekly" && <WeeklyView />}
        {viewMode === "monthly" && <MonthlyView />}
      </div>
    </div>
  );
}