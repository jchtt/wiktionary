import java.io.*;
import de.tudarmstadt.ukp.jwktl.*;
import de.tudarmstadt.ukp.jwktl.api.*;
import de.tudarmstadt.ukp.jwktl.api.util.*;
import info.bliki.wiki.model.WikiModel;

public class Convert
{
	public static void main(String[] args) throws Exception {
		File outputDirectory = new File("/data/Development/Wiktionary/jwktl/db");
		IWiktionaryEdition wkt = JWKTL.openEdition(outputDirectory);
		
		// Do stuff

		IWiktionaryPage page = wkt.getPageForWord("derive");
		IWiktionaryEntry entry = page.getEntry(0);
		IWiktionarySense sense = entry.getSense(1);

		System.out.println(convertToYaml(page));

		// if (sense.getExamples() != null)
		// 	for (IWikiString example : sense.getExamples())
		// 		System.out.println(example.getText());
		//

		// System.out.println(sense.getGloss().getText());

		// Quotations.
		// if (sense.getQuotations() != null)
		// 	for (IQuotation quotation : sense.getQuotations()) {
		// 		for (IWikiString line : quotation.getLines())
		// 			System.out.println(line.getText());
		// 		// System.out.println("--" + quotation.getSource().getText());
		// 	}

		// for (IPronunciation pron : entry.getPronunciations()) {
		// 	System.out.println(pron.getNote());
		// 	System.out.println(pron.getText());
		// }

		// System.out.println(entry.getWordEtymology().getText());

		// for (IWiktionaryWordForm form : entry.getWordForms()) {
		// 	System.out.println(form.getWordForm());
		// }

		
		// Print the default charset
		// System.out.println(java.nio.charset.Charset.defaultCharset());
		String strFilename = "/data/Development/Wiktionary/jwktl/yaml/test.yaml";
			String message = "Hello, world!\nHello, world again!\n";  // 2 lines of texts";

		try (BufferedWriter out = new BufferedWriter(new FileWriter(strFilename))) {
			out.write(message);
			out.flush();
		} catch (IOException ex) {
			ex.printStackTrace();
		}

		String htmlText = WikiModel.toHtml("This is a simple [[Hello World]] wiki tag");
		System.out.println(htmlText);

		wkt.close();
	}

	public static String convertToYaml(IWiktionaryPage page) {
		StringBuffer output = new StringBuffer();
		int indent = 0;
		int indentInc = 2;
		int dashInc = 2;
		output.append(indent(indent, "- title: " + page.getTitle()));
		indent += dashInc;
		output.append(indent(indent, "entries:\n"));
		indent += indentInc;
		
		for (IWiktionaryEntry entry : page.getEntries()) {
			if (entry.getWordLanguage() != Language.ENGLISH)
				continue;

			output.append(indent(indent, "- word: " + entry.getWord()));
			indent += dashInc;

			// Pronunciations
			if (entry.getPronunciations() != null) {
				output.append(indent(indent, "pronunciations:"));
				indent += indentInc;
				for (IPronunciation pron : entry.getPronunciations()) {
					output.append(indent(indent, "- note: " + pron.getNote()));
					indent += indentInc;
					output.append(indent(indent, "text: " + pron.getText()));
					indent -= indentInc;
				}
				indent -= indentInc;
			}

			// Part(s) of speech
			if (entry.getPartsOfSpeech() != null) {
				add(output, indent, "partsOfSpeech:");
				indent += indentInc;
				for (PartOfSpeech part : entry.getPartsOfSpeech()) {
					add(output, indent, "- " + part.toString().toLowerCase());
				}
				indent -= indentInc;
			}

			// Word forms
			if (entry.getWordForms() != null) {
				add(output, indent, "wordForms:");
				indent += indentInc;
				for (IWiktionaryWordForm form : entry.getWordForms()) {
					add(output, indent, "- form: " + form.getWordForm());
					indent += dashInc;
					if (form.getAspect() != null)
						add(output, indent, "aspect: " + form.getAspect().toString().toLowerCase());
					if (form.getDegree() != null)
						add(output, indent, "degree: " + form.getDegree().toString().toLowerCase());
					if (form.getMood() != null)
						add(output, indent, "mood: " + form.getMood().toString().toLowerCase());
					if (form.getNonFiniteForm() != null)
						add(output, indent, "nonFiniteForm: " + form.getNonFiniteForm().toString().toLowerCase());
					if (form.getNumber() != null)
						add(output, indent, "number: " + form.getNumber().toString().toLowerCase());
					if (form.getPerson() != null)
						add(output, indent, "person: " + form.getPerson().toString().toLowerCase());
					if (form.getTense() != null)
						add(output, indent, "number: " + form.getTense().toString().toLowerCase());
					indent -= dashInc;
				}
				indent -= indentInc;
			}

			// Etymology
			if (entry.getWordEtymology() != null) {
				add(output, indent, "etymology : |");
				indent += indentInc;
				add(output, indent, entry.getWordEtymology().getText());
				indent -= indentInc;
			}

			// Gender
			if (entry.getGender() != null) {
				add(output, indent, "gender: " + entry.getGender().toString());
			}

			// Senses
			if (entry.getSenses() != null) {
				add(output, indent, "senses:");
				indent += indentInc;
				for (IWiktionarySense sense : entry.getSenses()) {
					add(output, indent, "- gloss : |");
					indent += dashInc;
					indent += indentInc;
					add(output, indent, sense.getGloss().getText());
					indent -= indentInc;

					// Quotations
					if (sense.getQuotations() != null) {
						add(output, indent, "quotations: ");
						indent += indentInc;
						for (IQuotation quote : sense.getQuotations()) {
							String quoteString = "";
							for (IWikiString line : quote.getLines()) {
								quoteString += line.getText() + "\n";
							}
							add(output, indent, "- quote: |");
							indent += dashInc;
							add(output, indent, quoteString);
							indent -= dashInc;
						}
						indent -= indentInc;
					}

					if (sense.getExamples() != null) {
						add(output, indent, "examples:");
						indent += indentInc;
						for (IWikiString example : sense.getExamples()) {
							add(output, indent, "- example: |");
							indent += indentInc;
							add(output, indent, example.getText());
							indent -= indentInc;
						}
						indent -= indentInc;
					}

					indent -= dashInc;
				}
				indent -= indentInc;
			}

			indent -= indentInc;
		}

		// output.append(indent(indent, "
		return output.toString();
	}

	public static String indent(int indent, String str) {
		String lines[] = str.split("\\r?\\n");
		String output = "";
		String padding = "";
		for (int i = 0; i < indent; i++) {
			padding += " ";
		}

		for(String s : lines) {
			output += padding + s + "\n";
		}
		return output;
	}

	public static void add(StringBuffer buf, int indent, String s) {
		buf.append(indent(indent, s));
	}
}
