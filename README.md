traclib
=======

Python Library for accessing Trac (enhanced wiki and issue tracking system for software development projects)


Common Usages (class TracTicket)
*set_in_progress
 * set_under_review
 * set_under_test (must set TracTicket qa_tester property)
 * close
 * attach_diff (yes, upload and attach diff files)
 
Trac Ticket Specifics (TracTicketPage)
 * set_percent_complete
 * set_development_status
 * leave_as_assigned
 * resolve_as
 * reassign_to
 * accept
 * set_comment
 * submit_changes
 * 
