task context define po childdepth:0 or childdepth: 
task context define gpo gcode.not: and childdepth:0 or gcode.not: and childdepth:
task context define pend status:pending or status:waiting
task context define comp status:completed

task context define later +later
task context define blk +blk
task context define plan +plan
task context define wait +wait
task context define del +ar +del
task context define del1 +ar +del -obj
task context define ar +ar -del -later -plan -blk -wait
task context define ar1 +ar -del -later -plan -blk -wait -obj
task context define inv +inv -mile
task context define mile +mile -ar
task context define armile +mile +ar

task context define meet +inv +meeting -ar -obj
task context define armeet +inv +meeting +ar -obj
task context define act +inv +act -ar -obj
task context define aract +inv +act +ar -obj
task context define shop +inv +shop -ar
task context define arshop +inv +shop +ar
task context define dummy +inv +dummy
task context define proj +inv +proj +gcode -ar -obj
task context define arproj +inv +proj +gcode +ar -obj
task context define obj \( +inv +obj -ar \) or \( childdepth:0 and -ar \)
task context define arobj \( +inv +obj +ar \) or \( childdepth:0 and +ar \)
task context define delobj \( +inv +obj +del \) or \( childdepth:0 and +del \)
task context define projobj \( +inv +obj +proj \) or \( childdepth:0 and +proj \)

task context define viz -ar -inv and \(status:pending or status:waiting\)
task context define cur -ar -inv -obj
task context define curpo -ar -inv and \(childdepth:0 or childdepth: \)
task context define pri ppri.not: or gpri.not:
task context define ppri ppri.not:


task context define due due.not: -ar -del
task context define ddue due.after:today
task context define wkdue due.after:monday-7d
task context define 2wkdue due.after:monday-14d
task context define modue due.after:monday-30d

task context define alldone status:copmleted
task context define wkdone status:completed and end.after:now-1wk
task context define 2wkdone status:completed and end.after:now-2wk
task context define modone status:completed and end.after:now-1mo
task context define 2modone status:completed and end.after:now-2mo
