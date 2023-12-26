
// -------------------------------------------------------------
// - Sort -
// -------------------------------------------------------------
#define REPORT_SORT_MAIN   end+/,start+/,desort-/,priority+/,ppri+/,due+/,modified-/,scheduled-/,gcode+/,gpri+/,project+/,description+,
#define REPORT_SORT_MODIF  end+/,start+/,desort-/,modified-/,priority+/,ppri+/,due+/,scheduled-/,gcode+/,gpri+/,project+/,description+,
#define REPORT_SORT_OBJ    end+/,start+/,desort-/,childdepth+/,priority+/,ppri+/,gpri+/,due+/,modified-/,scheduled-/,gcode+/,project+/,description+,
#define REPORT_SORT_DUE_H  end+/,start+/,desort-/,due+/,priority+/,ppri+/,gcode+/,gpri+/,scheduled-/,project+/,description+
#define REPORT_SORT_SCH_L  end+/,start+/,desort-/,scheduled-/,due+/,priority+/,ppri+/,gcode+/,gpri+/,project+/,description+,
#define REPORT_SORT_EST_L  end+/,start+/,desort-/,priority+/,ppri+/,gcode+/,gpri+/,due+/,scheduled-/,project+/,blkest+/,description+
#define REPORT_SORT_EST_H  end+/,start+/,desort-/,blkest+/,priority+/,ppri+/,gcode+/,gpri+/,due+/,scheduled-/,project+/,description+
#define REPORT_SORT_PRI_H  end+/,start+/,desort-/,ppri+/,priority+/,gcode+/,gpri+/,due+/,scheduled-/,project+/,description+
#define REPORT_SORT_GCODE  end+/,start+/,desort-/,gcode+/,gpri+/,priority+/,ppri+/,due+/,scheduled-/,project+/,description+,
#define REPORT_SORT_DONE   end+/,
//#define REPORT_SORT_DONE   end+/,start+/,desort-/,priority+/,ppri+/,gcode+/,gpri+/,due+/,scheduled+/,project+/,description+


// -------------------------------------------------------------
// - Filteryer onjk -
// -------------------------------------------------------------

#define REPORT_FILTER_COMPLETED_IN_A_WEEK (status:completed and end.after:now-1wk)
#define REPORT_FILTER_PENDING (status:pending or status:waiting)
#define REPORT_FILTER_STATUS(X) (REPORT_FILTER_PENDING or X)
//        REPORT_FILTER_STATUS(REPORT_FILTER_COMPLETED_IN_A_WEEK)

#define REPORT_FILTER_HIDE (-inv and -ar)
#define REPORT_FILTER_STARTED start.not:
#define REPORT_FILTER_STARTED_AND(X) REPORT_FILTER_STARTED and X

#define REPORT_FILTER_CURMIN REPORT_FILTER_STARTED or (REPORT_FILTER_HIDE and REPORT_FILTER_PENDING)
#define REPORT_FILTER_CURMIN_WITH(X) REPORT_FILTER_STARTED or (REPORT_FILTER_HIDE and REPORT_FILTER_PENDING and X)


// -------------------------------------------------------------
// - Columns/Labels -
// -------------------------------------------------------------

// in vim, :set nowrap to view lines horizontally

#define REPORT_MAIN_LABELS UUID,       Compl, dTs,       PPri, GPri, Sch,                Due, Rem,    Put,    GCode,  Project, Description
#define REPORT_MAIN_COLMNS uuid.short, end,   start.age, ppri, gpri, scheduled.relative, due, blkrem, blkputcum, gcode,  project, description.count

#define REPORT_MODIFIED_LABELS UUID,       Compl, Modified, dTs,       PPri, GPri, Sch,                Due, Rem,    Put,    GCode,  Project, Description
#define REPORT_MODIFIED_COLMNS uuid.short, end,   modified, start.age, ppri, gpri, scheduled.relative, due, blkrem, blkputcum, gcode,  project, description.count

#define REPORT_ESTMIN_LABELS UUID,       Compl, dTs,       PPri, GPri, Sch,                Due, Rem,    Put,    GCode, Project, Description
#define REPORT_ESTMIN_COLMNS uuid.short, end,   start.age, ppri, gpri, scheduled.relative, due, blkrem, blkputcum, gcode, project, description.count


// -------------------------------------------------------------
// - Main Reports -
// -------------------------------------------------------------

report.all.labels           =REPORT_MAIN_LABELS
report.all.columns          =REPORT_MAIN_COLMNS
report.all.description      =All items, no filters applied
report.all.filter           =
report.all.sort             =status-/,REPORT_SORT_MAIN

report.main.labels          =REPORT_MAIN_LABELS
report.main.columns         =REPORT_MAIN_COLMNS
report.main.description     =Main report view. Does not show objectives.
report.main.filter          =-obj and (REPORT_FILTER_STARTED or REPORT_FILTER_PENDING)
report.main.sort            =status-/,REPORT_SORT_MAIN

report.obj.labels           =REPORT_MAIN_LABELS
report.obj.columns          =REPORT_MAIN_COLMNS
report.obj.description      =Tasks and their objectives
report.obj.filter           =REPORT_FILTER_STARTED or REPORT_FILTER_PENDING
report.obj.sort             =status-/,REPORT_SORT_OBJ

report.modif.labels         =REPORT_MODIFIED_LABELS
report.modif.columns        =REPORT_MODIFIED_COLMNS
report.modif.description    =All Tasks (no filters except not completed) in minimum entry style
report.modif.filter         =REPORT_FILTER_STARTED or REPORT_FILTER_PENDING
report.modif.sort           =status-/,REPORT_SORT_MODIF

// -------------------------------------------------------------
// - Alternative Analysis -
// -------------------------------------------------------------

// -------------------------------------------------------------
// - Alternative Sortings -
// -------------------------------------------------------------

report.nosort.labels           =REPORT_MAIN_LABELS
report.nosort.columns          =REPORT_MAIN_COLMNS
report.nosort.description      =All Tasks (no filters except not completed) in minimum entry style
report.nosort.filter           =REPORT_FILTER_STARTED or REPORT_FILTER_PENDING
report.nosort.sort             =

report.sortdue.labels          =REPORT_MAIN_LABELS
report.sortdue.columns         =REPORT_MAIN_COLMNS
report.sortdue.description     =Curretn tasks, sorted by due date
report.sortdue.filter          =REPORT_FILTER_CURMIN_WITH(due.not:)
report.sortdue.sort            =REPORT_SORT_DUE_H

report.sortsch.labels          =REPORT_MAIN_LABELS
report.sortsch.columns         =REPORT_MAIN_COLMNS
report.sortsch.description     =Curretn tasks, sorted by schedule
report.sortsch.filter          =REPORT_FILTER_CURMIN_WITH(sch.not:)
report.sortsch.sort            =REPORT_SORT_SCH_L

report.sortest.labels          =REPORT_ESTMIN_LABELS
report.sortest.columns         =REPORT_ESTMIN_COLMNS
report.sortest.description     =Current Tasks displaying their estimated time to completion
report.sortest.filter          =REPORT_FILTER_CURMIN_WITH(blkest.not:)
report.sortest.sort            =REPORT_SORT_EST_H

report.sortpri.labels          =REPORT_MAIN_LABELS
report.sortpri.columns         =REPORT_MAIN_COLMNS
report.sortpri.description     =Sort report by ppri
report.sortpri.filter          =REPORT_FILTER_CURMIN_WITH(ppri.not:)
report.sortpri.sort            =REPORT_SORT_PRI_H

report.sortg.labels            =REPORT_MAIN_LABELS
report.sortg.columns           =REPORT_MAIN_COLMNS
report.sortg.description       =Curretn tasks, sorted by gcode
report.sortg.filter            =REPORT_FILTER_CURMIN_WITH(gcode.not:)
report.sortg.sort              =REPORT_SORT_GCODE


// -------------------------------------------------------------
// - Complete Reports -
// -------------------------------------------------------------

report.wkdone.labels          =REPORT_MAIN_LABELS
report.wkdone.columns         =REPORT_MAIN_COLMNS
report.wkdone.description     =Completed Tasks within last week
report.wkdone.filter          =REPORT_FILTER_STARTED or (status:completed and end.after:now-1wk)
report.wkdone.sort            =REPORT_SORT_DONE

report.2wkdone.labels         =REPORT_MAIN_LABELS
report.2wkdone.columns        =REPORT_MAIN_COLMNS
report.2wkdone.description    =Completed Tasks within last 2 weeks
report.2wkdone.filter         =REPORT_FILTER_STARTED or (status:completed and end.after:now-2wk)
report.2wkdone.sort           =REPORT_SORT_DONE

report.modone.labels          =REPORT_MAIN_LABELS
report.modone.columns         =REPORT_MAIN_COLMNS
report.modone.description     =Completed Tasks within last month
report.modone.filter          =REPORT_FILTER_STARTED or (status:completed and end.after:now-1mo)
report.modone.sort            =REPORT_SORT_DONE

report.3modone.labels         =REPORT_MAIN_LABELS
report.3modone.columns        =REPORT_MAIN_COLMNS
report.3modone.description    =Completed Tasks within last month
report.3modone.filter         =REPORT_FILTER_STARTED or (status:completed and end.after:now-3mo)
report.3modone.sort           =REPORT_SORT_DONE

report.alldone.labels            =REPORT_MAIN_LABELS
report.alldone.columns           =REPORT_MAIN_COLMNS
report.alldone.description       =Completed Tasks in minimum entry style (no logs)
report.alldone.filter            =REPORT_FILTER_STARTED or (status:completed)
report.alldone.sort              =REPORT_SORT_DONE

// -------------------------------------------------------------
// - Other Reports -
// -------------------------------------------------------------

report.delmin.labels          =REPORT_MAIN_LABELS
report.delmin.columns         =REPORT_MAIN_COLMNS
report.delmin.description     =Deleted Tasks
report.delmin.filter          =status:deleted
report.delmin.sort            =REPORT_SORT_MAIN

// -------------------------------------------------------------
// - Inactive Reports -
// -------------------------------------------------------------
