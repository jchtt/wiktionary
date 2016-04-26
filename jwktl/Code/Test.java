import java.io.*;
import de.tudarmstadt.ukp.jwktl.*;
import de.tudarmstadt.ukp.jwktl.api.*;

public class Test
{
	public static void main(String[] args) throws Exception {
		File outputDirectory = new File("/data/Development/Wiktionary/jwktl/db");
		IWiktionaryEdition wkt = JWKTL.openEdition(outputDirectory);
		
		// Do stuff

		IWiktionaryPage page = wkt.getPageForWord("derive");
		IWiktionaryEntry entry = page.getEntry(0);
		IWiktionarySense sense = entry.getSense(1);

		// if (sense.getExamples() != null)
		// 	for (IWikiString example : sense.getExamples())
		// 		System.out.println(example.getText());
		//

		System.out.println(sense.getGloss().getText());

		// Quotations.
		if (sense.getQuotations() != null)
			for (IQuotation quotation : sense.getQuotations()) {
				for (IWikiString line : quotation.getLines())
					System.out.println(line.getText());
				// System.out.println("--" + quotation.getSource().getText());
			}

		for (IPronunciation pron : entry.getPronunciations()) {
			System.out.println(pron.getNote());
			System.out.println(pron.getText());
		}

		System.out.println(entry.getWordEtymology().getText());

		for (IWiktionaryWordForm form : entry.getWordForms()) {
			System.out.println(form.getWordForm());
		}

		
		wkt.close();
	}
}
