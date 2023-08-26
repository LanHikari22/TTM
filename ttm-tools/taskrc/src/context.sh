task context define later +later
task context define blk +blk
task context define del +ar +del
task context define del1 +ar +del -obj
task context define ar +ar -del -later -blk
task context define ar1 +ar -del -later -blk -wait -obj
task context define arr +ar
task context define inv +inv -mile
task context define mile +mile -ar
task context define armile +mile +ar

task context define area +inv +area -ar -obj
task context define ararea +inv +area +ar -obj
task context define res +inv +res -ar -obj
task context define arres +inv +res -ar -obj
task context define dummy +inv +dummy
task context define gcode +inv +gcode -ar -obj
task context define argcode +inv +gcode +ar -obj
task context define obj \( +inv +obj -ar \) or \( childdepth:0 and -ar \)

task context define proj -ar -inv -obj
task context define pri ppri.not: or gpri.not:
task context define ppri ppri.not:

task context define due due.not: -ar -del
