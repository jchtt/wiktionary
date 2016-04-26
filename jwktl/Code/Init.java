import java.io.*;
import de.tudarmstadt.ukp.jwktl.*;

public class Init
{
	public static void main(String[] args) throws Exception {
		File dumpFile = new File("enwiktionary-latest-pages-articles.xml");
		File outputDirectory = new File("/data/Development/Wiktionary/jwktl/db");
		boolean overwriteExisting = true;

		JWKTL.parseWiktionaryDump(dumpFile, outputDirectory, overwriteExisting);
	}
}
