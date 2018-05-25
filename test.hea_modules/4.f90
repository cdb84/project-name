program hello
implicit none
character (len=:), allocatable :: hw

hw = "Hello World!"

WRITE(6,*) reverse(hw, LEN(HW))

contains

function reverse(in_str, str_length)
implicit none

character (len =:), allocatable :: reverse

integer :: str_length, n
character (len=:), allocatable :: in_str
character :: swap_char

do n = str_length,1,-1
   swap_char = in_str(n:n)
   reverse = reverse//swap_char
end do
end function reverse
end program hello

