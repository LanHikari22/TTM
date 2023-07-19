#include "taskrc_settings.cpp"
#include "taskrc_reports.cpp"

// -------------------------------------------------------------
// UDA
// -------------------------------------------------------------

// (Calculated) Current Time performed against this task
uda.blkput.type=numeric
uda.blkput.label=Put

// Manual Current time performed against this task. This will be added to tracked calculated time.
uda.blkputman.type=numeric
uda.blkputman.label=Put

// Cumulative Time performed against this task (Including subtasks, put+sub)
uda.blkputcum.type=numeric
uda.blkputcum.label=Put

// Estimated time to complete task (in multiples of some 20 minutes)
uda.blkest.type=numeric
uda.blkest.label=Est

// (CalculateD) Remaining Estimated time to complete task (in multiples of some 20 minutes)
uda.blkrem.type=numeric
uda.blkrem.label=Est

// Aggregate estimated time to complete task (Including subtasks, all+sub)
uda.blkestcum.type=numeric
uda.blkestcum.label=Est

// Schedule End Time
uda.endsch.type=date
uda.endsch.label=EndSch

// Event tag when adding an event. By defualt it is just EVNT.
uda.etag.type=string
uda.etag.label=EventTag
uda.etag.default=EVNT


// task size -- Agile

uda.size.type=string
uda.size.label=Siz
uda.size.values=S,M,L,XL,2XL

// collection of notes or resources linked to a task
uda.notelinks.type=string
uda.notelinks.label=NLinks

// colletion of issue ids for other issue trackers
uda.issuelinks.type=string
uda.issuelinks.label=ILinks

// associated tasks that may describe it more such as ideas, project milestones, etc
uda.linkedto.type=string
uda.linkedto.label=LinkedTo

// subtask identification -- children point to parent, parent points to children 
uda.childof.type=string
uda.childof.label=Parent

uda.children.type=string
uda.children.label=Children

uda.childdepth.type=numeric
uda.childdepth.label=Ancestors
uda.childdepth.default=0

// task scheduling
uda.expdur.type=numeric
uda.expdur.label=expdur
uda.expdur.default=0

uda.durunit.type=string
uda.durunit.label=durunit
uda.durunit.values=1m,15m,20m,1h
uda.durunit.default=1h

// Z priority is the same as L, just clearly in alphabetical order
uda.priority.values=H,M,L,Z
color.uda.priority.Z=color245
urgency.uda.priority.Z.coefficient=1.8

// priority number. To order items within the same priority value
uda.ppri.type=numeric
uda.ppri.label=ppri
uda.ppri.default=

// Goal-relative priority number.
uda.gpri.type=numeric
uda.gpri.label=gpri
uda.gpri.default=

uda.state.type=string
uda.state.default=

// Goal Code. Different tasks can share this code as belonging to the same goal.
// Typically used for tracking tasks that count within the same focus or time spending.
// Can also be used to detonate milestones. It needs to have a unique extenstion for that.
uda.gcode.type=string
uda.gcode.label=GCode
uda.gcode.default=

// sort last
uda.desort.type=string
uda.desort.default=

// -------------------------------------------------------------
// Data formats
// -------------------------------------------------------------

// date format config
// dateformat=[yMD a]
// dateformat=[yWV a]
// dateformat=y_WVa
dateformat=yMD-WVa

