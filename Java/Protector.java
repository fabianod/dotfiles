// FILE INPUT AND OUTPUT
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.File;
import java.io.FileWriter;

// CIPHER AND GENERATORS
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.KeyGenerator;

// KEY SPECIFICATIONS
import java.security.spec.KeySpec;
import java.security.spec.AlgorithmParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEParameterSpec;

/**
 * Written by Ryan D'souza
 *
 * Encrypts and decrypts textfiles/strings using AES 128 byte + a salt
 * Uses no external libraries - lightweight and quick to use
 *
 * Run Instructions: 
 *  1. javac Protector.java
 *  2. java Protector
*/

public class Protector {

    //Constants used in algorithm
    private static final String ALGO = "AES";
    private static final String KEY_INSTANCE = "PBEWithMD5AndDES";
    private static final String ENCODING = "UTF8";
    private static final String VALIDATION = "QFyeiIhC7Wmk2F6";

    //Responsible for encrypting/decrypting
    private Cipher encryptCipher;
    private Cipher decryptCipher;
    
    /**
     * Constructor - password as plain text
    */
    public Protector(final String password) {

        final byte[] salt = generateSalt();
        final int iterationCount = 19;

        //Creates the encrypter and decrypter cipher with AES algorithm + salt
        try {
            final KeySpec keySpec = new PBEKeySpec(password.toCharArray(), salt, iterationCount);
            final SecretKey key = SecretKeyFactory.getInstance(KEY_INSTANCE).generateSecret(keySpec);
            final AlgorithmParameterSpec paramSpec = new PBEParameterSpec(salt, iterationCount);

            this.encryptCipher = Cipher.getInstance(key.getAlgorithm());
            this.encryptCipher.init(Cipher.ENCRYPT_MODE, key, paramSpec);

            this.decryptCipher = Cipher.getInstance(key.getAlgorithm());
            this.decryptCipher.init(Cipher.DECRYPT_MODE, key, paramSpec);
        }

        catch(Exception e) {
            e.printStackTrace();
        }
    }

    /** Returns a random salt */
    private static byte[] generateSalt() {
        final byte[] salt = {
            (byte)0xA9, (byte)0x9B, (byte)0xC8, (byte)0x32,
            (byte)0x56, (byte)0x34, (byte)0xE3, (byte)0x03
        };
        return salt;
    }

    /** Given a string, decrypts it using the decryption cipher */
    public String decrypt(final String encrypted) {
        try {

            // Decode base64 to get bytes
            byte[] dec = new sun.misc.BASE64Decoder().decodeBuffer(encrypted);

            // Decrypt
            byte[] utf8 = this.decryptCipher.doFinal(dec);

            // Decode using utf-8
            return new String(utf8, ENCODING);
        }
        catch(Exception e) {
            e.printStackTrace();
            return e.toString();
        }
    }

    /** Given a string, encrypts it using the encrypton cipher */
    public String encrypt(final String unencrypted) {
        try {

            // Encode the string into bytes using utf-8
            byte[] utf8 = unencrypted.getBytes(ENCODING);

            // Encrypt
            byte[] enc = this.encryptCipher.doFinal(utf8);

            return new sun.misc.BASE64Encoder().encode(enc);

        }
        catch(Exception e) {
            e.printStackTrace();
            return e.toString();
        }
    }

    /** Encrypts a text file */
    public void encryptTextFile(final String fileName) {

        //Get the contents of the textfile, and append a validation token to it
        final String unencrypted = VALIDATION + getTextFromFile(fileName);

        //Encrypt the validation and contents of textfile
        final String encrypted = this.encrypt(unencrypted);

        //Overwrite that textfile with the encrypted contents
        writeToTextFile(fileName, encrypted);
    }

    /** Checks the validity of a decrypted string */
    public static boolean isValid(final String text) {

        //If it's shorter than our validation token
        if(text.length() < VALIDATION.length()) {
            return false;
        }

        //The first X characters should equal our validation 
        final String firstFew = text.substring(0, VALIDATION.length());
        return firstFew.equals(VALIDATION);
    }

    /** Decrypts a textfile using the decrypt cipher. Decryption can fail */
    public boolean decryptTextFile(final String fileName) {

        //Encrypted text from file
        final String encrypted = getTextFromFile(fileName);

        //Decrypt all of the encrypted text
        String decrypted = this.decrypt(encrypted);

        //If it's not a valid decryption cipher - incorrect password
        if(!isValid(decrypted)) {
            System.out.println("Incorrect decryption for: " + fileName);
            return false;
        }

        //If it is valid, remove the validator, overwrite the textfile with unencrypted
        decrypted = decrypted.substring(VALIDATION.length());
        writeToTextFile(fileName, decrypted);
        return true;
    }

    /** Returns the text in a file */
    public static String getTextFromFile(final String fileName) {

        String result = "";
        try {
            final BufferedReader reader = new BufferedReader(new FileReader(fileName));

            String line = "";

            while((line = reader.readLine()) != null) {
                result += line + "\n"; //For formatting
            }
            
            reader.close();
        }
        catch(Exception e) {
            e.printStackTrace();
        }

        return result;
    }

    /** Overwrites the contents of a textfile with the text paramater */
    public static void writeToTextFile(final String fileName, final String text) {

        try {
            final FileWriter writer = new FileWriter(new File(fileName), false);
            writer.write(text);
            writer.close();
        }
        catch(Exception e) {
            e.printStackTrace();
        }
    }

    /** Prompts the user to encrypt or decrypt */
    public static boolean userWantsToEncrypt() {
        System.out.println("Enter E to Encrypt or D to Decrypt: ");
        final String input = System.console().readLine();
        return input.equalsIgnoreCase("e") || input.equalsIgnoreCase("encrypt");
    }

    /** Prompts the user for a file name */
    public static String getFileNameFromUser() {
        System.out.println("Enter file name: ");
        return System.console().readLine();
    }

    /** Prompts the user for a password */
    public static String getPasswordFromUser() {
        System.out.println("Enter password: ");
        final String firstPass = new String(System.console().readPassword());

        /*System.out.println("Confirm: ");
        final String secondPass = new String(System.console().readPassword());

        //Passwords don't match
        if(!firstPass.equals(secondPass)) {
            System.out.println("Not equal passwords. Re-enter");
            return getPasswordFromUser();
        } */

        return firstPass;
    }

    /** For testing */
    public static void main(String[] ryan) {

        //Object created with inputted password
        Protector protector = new Protector(getPasswordFromUser());

        //If the user didn't put a file name as a parameter, prompt for it
        final String fileName = ryan.length > 0 ? ryan[0] : getFileNameFromUser();

        //If the user didn't specify encryption/decryption, prompt for it
        final boolean toEncrypt = ryan.length > 1 ? ryan[1].equalsIgnoreCase("e") || ryan[1].equalsIgnoreCase("encrypt") : userWantsToEncrypt();

        if(toEncrypt) {
            protector.encryptTextFile(fileName);
            System.out.println("Successfully encrypted: " + fileName);
        }
        else {
            if(protector.decryptTextFile(fileName)) {
                System.out.println("Successfully decrypted: " + fileName);
            }
            else {
                System.out.println("Decryption for: " + fileName + " failed");
            }
        }
    }
}
