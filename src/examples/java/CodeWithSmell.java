package examples.java;

public class CodeWithSmell {
    private static int timeout = 10;

    public static void main(String[] args) {
        compute();
    }

    private static long compute() {
        long total = 0;
        for (int i = 0; i < 1_000_000; i++) {
            total += timeout * i;
        }
        return total;
    }
}