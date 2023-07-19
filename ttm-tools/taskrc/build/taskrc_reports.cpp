
# -------------------------------------------------------------
# - Sort -
# -------------------------------------------------------------
#define REPORT_SORT_TMPL1  ,end+/,start+/,desort-/,priority+/,ppri+/,gcode+/,gpri+/,due+/,scheduled+/,project+/,description+,
#define REPORT_SORT_DUE_H  ,end+/,start+/,desort-/,due+/,priority+/,ppri+/,gcode+/,gpri+/,scheduled+/,project+/,description+
#define REPORT_SORT_EST_L  ,end+/,start+/,desort-/,priority+/,ppri+/,gcode+/,gpri+/,due+/,scheduled+/,project+/,blkest+/,description+
#define REPORT_SORT_EST_H  ,end+/,start+/,desort-/,blkest+/,priority+/,ppri+/,gcode+/,gpri+/,due+/,scheduled+/,project+/,description+
#define REPORT_SORT_PRI_H  ,end+/,start+/,desort-/,ppri+/,priority+/,gcode+/,gpri+/,due+/,scheduled+/,project+/,description+
#define REPORT_SORT_DONE   ,end+/,
##define REPORT_SORT_DONE   end+/,start+/,desort-/,priority+/,ppri+/,gcode+/,gpri+/,due+/,scheduled+/,project+/,description+


# -------------------------------------------------------------
# - Filter -
# -------------------------------------------------------------

#define REPORT_FILTER_COMPLETED_IN_A_WEEK (status:completed and end.after:now-1wk)
#define REPORT_FILTER_PENDING (status:pending or status:waiting)
#define REPORT_FILTER_STATUS(X) (REPORT_FILTER_PENDING or X)
#        REPORT_FILTER_STATUS(REPORT_FILTER_COMPLETED_IN_A_WEEK)

#define REPORT_FILTER_HIDE (-inv and -ar)
#define REPORT_FILTER_STARTED start.not:
#define REPORT_FILTER_STARTED_AND(X) REPORT_FILTER_STARTED and X

#define REPORT_FILTER_CURMIN REPORT_FILTER_STARTED or (REPORT_FILTER_HIDE and REPORT_FILTER_PENDING)
#define REPORT_FILTER_CURMIN_WITH(X) REPORT_FILTER_STARTED or (REPORT_FILTER_HIDE and REPORT_FILTER_PENDING and X)


# -------------------------------------------------------------
# - Columns/Labels -
# -------------------------------------------------------------

# in vim,:set nowrap to view lines horizontally

#define REPORT_CURMIN_LABELS UUID,Compl,dTs,PPri,GPri,Sch,Due,Rem,Put,GCode,Project,Description
#define REPORT_CURMIN_COLMNS uuid.short,end,start.age,ppri,gpri,scheduled.relative,due,blkrem,blkputcum,gcode,project,description.count

#define REPORT_ESTMIN_LABELS UUID,Compl,dTs,PPri,GPri,Sch,Due,Rem,Put,GCode,Project,Description
#define REPORT_ESTMIN_COLMNS uuid.short,end,start.age,ppri,gpri,scheduled.relative,due,blkrem,blkputcum,gcode,project,description.count


# -------------------------------------------------------------
# - Main Reports -
# -------------------------------------------------------------

report.curmin.labels          =REPORT_CURMIN_LABELS
report.curmin.columns         =REPORT_CURMIN_COLMNS
report.curmin.description     =Current Tasks in minimum entry style (no logs)
report.curmin.filter          =REPORT_FILTER_CURMIN
report.curmin.sort            =REPORT_SORT_TMPL1

report.invmin.labels          =REPORT_CURMIN_LABELS
report.invmin.columns         =REPORT_CURMIN_COLMNS
report.invmin.description     =Displays Tasks (including ones marked -inv) in minimum entry style
report.invmin.filter          =REPORT_FILTER_STARTED or (REPORT_FILTER_PENDING and +inv)
report.invmin.sort            =REPORT_SORT_TMPL1

report.armin.labels           =REPORT_CURMIN_LABELS
report.armin.columns          =REPORT_CURMIN_COLMNS
report.armin.description      =Displays Tasks (including ones marked -inv) in minimum entry style
report.armin.filter           =REPORT_FILTER_STARTED or (REPORT_FILTER_PENDING and +ar)
report.armin.sort             =REPORT_SORT_TMPL1

report.allmin.labels          =REPORT_CURMIN_LABELS
report.allmin.columns         =REPORT_CURMIN_COLMNS
report.allmin.description     =All Tasks (no filters) in minimum entry style
report.allmin.filter          =
report.allmin.sort            =status-/,REPORT_SORT_TMPL1

report.allcur.labels          =REPORT_CURMIN_LABELS
report.allcur.columns         =REPORT_CURMIN_COLMNS
report.allcur.description     =All Tasks (no filters except not completed) in minimum entry style
report.allcur.filter          =REPORT_FILTER_STARTED or REPORT_FILTER_PENDING
report.allcur.sort            =status-/,REPORT_SORT_TMPL1

# -------------------------------------------------------------
# - Alternative Analysis -
# -------------------------------------------------------------

# -------------------------------------------------------------
# - Alternative Sortings -
# -------------------------------------------------------------

report.nosort.labels          =REPORT_CURMIN_LABELS
report.nosort.columns         =REPORT_CURMIN_COLMNS
report.nosort.description     =All Tasks (no filters except not completed) in minimum entry style
report.nosort.filter          =REPORT_FILTER_STARTED or REPORT_FILTER_PENDING
report.nosort.sort            =

report.sortdue.labels          =REPORT_CURMIN_LABELS
report.sortdue.columns         =REPORT_CURMIN_COLMNS
report.sortdue.description     =Curretn tasks,sorted by due date
report.sortdue.filter          =REPORT_FILTER_CURMIN_WITH(due.not:)
report.sortdue.sort            =REPORT_SORT_DUE_H

report.sortest.labels          =REPORT_ESTMIN_LABELS
report.sortest.columns         =REPORT_ESTMIN_COLMNS
report.sortest.description     =Current Tasks displaying their estimated time to completion
report.sortest.filter          =REPORT_FILTER_CURMIN_WITH(blkest.not:)
report.sortest.sort            =REPORT_SORT_EST_H

report.sortpri.labels          =REPORT_CURMIN_LABELS
report.sortpri.columns         =REPORT_CURMIN_COLMNS
report.sortpri.description     =Sort report by ppri
report.sortpri.filter          =REPORT_FILTER_CURMIN_WITH(ppri.not:)
report.sortpri.sort            =REPORT_SORT_PRI_H


# -------------------------------------------------------------
# - Complete Reports -
# -------------------------------------------------------------

report.wkdone.labels          =REPORT_CURMIN_LABELS
report.wkdone.columns         =REPORT_CURMIN_COLMNS
report.wkdone.description     =Completed Tasks within last week
report.wkdone.filter          =REPORT_FILTER_STARTED or (status:completed and end.after:now-1wk)
report.wkdone.sort            =REPORT_SORT_DONE

report.2wkdone.labels         =REPORT_CURMIN_LABELS
report.2wkdone.columns        =REPORT_CURMIN_COLMNS
report.2wkdone.description    =Completed Tasks within last 2 weeks
report.2wkdone.filter         =REPORT_FILTER_STARTED or (status:completed and end.after:now-2wk)
report.2wkdone.sort           =REPORT_SORT_DONE

report.modone.labels          =REPORT_CURMIN_LABELS
report.modone.columns         =REPORT_CURMIN_COLMNS
report.modone.description     =Completed Tasks within last month
report.modone.filter          =REPORT_FILTER_STARTED or (status:completed and end.after:now-1mo)
report.modone.sort            =REPORT_SORT_DONE

report.3modone.labels         =REPORT_CURMIN_LABELS
report.3modone.columns        =REPORT_CURMIN_COLMNS
report.3modone.description    =Completed Tasks within last month
report.3modone.filter         =REPORT_FILTER_STARTED or (status:completed and end.after:now-3mo)
report.3modone.sort           =REPORT_SORT_DONE

report.alldone.labels         =REPORT_CURMIN_LABELS
report.alldone.columns        =REPORT_CURMIN_COLMNS
report.alldone.description    =Completed Tasks in minimum entry style (no logs)
report.alldone.filter         =REPORT_FILTER_STARTED or (status:completed)
report.alldone.sort           =REPORT_SORT_DONE

# -------------------------------------------------------------
# - Other Reports -
# -------------------------------------------------------------

report.delmin.labels          =REPORT_CURMIN_LABELS
report.delmin.columns         =REPORT_CURMIN_COLMNS
report.delmin.description     =Deleted Tasks
report.delmin.filter          =status:deleted
report.delmin.sort            =REPORT_SORT_TMPL1

# -------------------------------------------------------------
# - Inactive Reports -
# -------------------------------------------------------------

report.tagmin.labels          =UUID,Compl,dTs,Mod,Sch,Tags,Project,Description
report.tagmin.columns         =uuid.short,end,start.age,modified.age,scheduled.relative,tags.list,project,description.count
report.tagmin.description     =Minimal details of tasks (With Duration)
report.tagmin.filter          =status:pending or status:waiting or status:completed
report.tagmin.sort            =end-/,modified-/,tags-/,project+/,description+
