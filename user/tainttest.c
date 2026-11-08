
#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fcntl.h"

int
main(void)
{
  char buf[512];
  int fd, pid;

  // Test 1: Read trusted file
  fd = open("trusted.txt", O_RDONLY);

  if (fd < 0) {
    printf("Cannot open trusted.txt\n");
    exit(1);
  }

  read(fd, buf, sizeof(buf));
  close(fd);

  printf("Trusted file read successfully\n");

  fd = open("trusted_delete_test.txt", O_CREATE | O_WRONLY);

  if (fd < 0) {
    printf("Could not create test file\n");
    exit(1);
  }

  close(fd);

  if (unlink("trusted_delete_test.txt") == 0) {
    printf("PASS: Trusted read did not taint process\n");
  } else {
    printf("FAIL: Trusted read test\n");
    exit(1);
  }

  // Test 2: Read untrusted file
  fd = open("inbox.txt", O_RDONLY);

  if (fd < 0) {
    printf("Cannot open inbox.txt\n");
    exit(1);
  }

  read(fd, buf, sizeof(buf));
  close(fd);

  printf("Untrusted file read successfully\n");

  // Test 3: Benign operation after taint
  fd = open("tainted_benign.txt", O_CREATE | O_WRONLY);

  if (fd < 0) {
    printf("FAIL: Could not create file after taint\n");
    exit(1);
  }

  write(fd, "Benign operation allowed\n", 25);
  close(fd);

  printf("PASS: Benign operation allowed after taint\n");

  // Test 4: Check taint inheritance through fork
  pid = fork();

  if (pid < 0) {
    printf("Fork failed\n");
    exit(1);
  }

  if (pid == 0) {
    printf("Child process attempting deletion\n");

    if (unlink("important.txt") < 0) {
      printf("PASS: Kernel blocked deletion in child\n");
    } else {
      printf("FAIL: Important file was deleted\n");
    }

    exit(0);
  }

  wait(0);

  printf("Taint inheritance test completed\n");

  exit(0);
}
