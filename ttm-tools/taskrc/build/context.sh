task context define po childdepth:0 or childdepth:
task context define gpo gcode.not: and childdepth:0 or gcode.not: and childdepth:
task context define pend status:pending or status:waiting
task context define comp status:completed

task context define later +later
task context define blk +blk
task context define plan +plan
task context define wait +wait
task context define del +ar +del
task context define ar +ar -del -later -plan -blk -wait
task context define inv +inv -mile
task context define mile +mile -ar
task context define armile +mile +ar

task context define meet +inv +meeting
task context define meeting +inv +meeting
task context define act +inv +act
task context define shop +inv +shop

task context define viz -ar -inv and \(status:pending or status:waiting\)
task context define cur -ar -inv 
task context define pri ppri.not: or gpri.not:


task context define due due.not:
task context define ddue due.after:today
task context define wkdue due.after:monday-7d
task context define 2wkdue due.after:monday-14d
task context define modue due.after:monday-30d

task context define alldone status:copmleted
task context define wkdone status:completed and end.after:now-1wk
task context define 2wkdone status:completed and end.after:now-2wk
task context define modone status:completed and end.after:now-1mo
task context define 2modone status:completed and end.after:now-2mo
